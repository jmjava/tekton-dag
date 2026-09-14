package integration_test

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
	"github.com/jmjava/tekton-dag/operator/internal/controller"
	"github.com/jmjava/tekton-dag/operator/internal/pipeline"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
)

var (
	testEnv    *envtest.Environment
	testClient client.Client
	testScheme *runtime.Scheme
)

func TestMain(m *testing.M) {
	testScheme = runtime.NewScheme()
	if err := corev1.AddToScheme(testScheme); err != nil {
		panic(err)
	}
	if err := tektondagv1alpha1.AddToScheme(testScheme); err != nil {
		panic(err)
	}

	testEnv = &envtest.Environment{
		CRDDirectoryPaths: []string{
			filepath.Join("..", "..", "config", "crd", "bases"),
			filepath.Join("testdata"),
		},
		ErrorIfCRDPathMissing: true,
	}
	cfg, err := testEnv.Start()
	if err != nil {
		_, _ = fmt.Fprintf(os.Stderr, "start envtest: %v\n", err)
		os.Exit(1)
	}
	testClient, err = client.New(cfg, client.Options{Scheme: testScheme})
	if err != nil {
		_ = testEnv.Stop()
		panic(err)
	}

	code := m.Run()
	if err := testEnv.Stop(); err != nil {
		_, _ = fmt.Fprintf(os.Stderr, "stop envtest: %v\n", err)
		code = 1
	}
	os.Exit(code)
}

func TestStackRunDomainLifecycle(t *testing.T) {
	ctx := context.Background()
	namespace := &corev1.Namespace{ObjectMeta: metav1.ObjectMeta{
		GenerateName: "stackrun-domain-",
	}}
	if err := testClient.Create(ctx, namespace); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = testClient.Delete(ctx, namespace) })

	stack := &tektondagv1alpha1.Stack{
		ObjectMeta: metav1.ObjectMeta{Name: "stack-one", Namespace: namespace.Name},
		Spec: tektondagv1alpha1.StackSpec{
			Name:      "stack-one",
			StackFile: "stacks/stack-one.yaml",
			GitURL:    "https://github.com/example/platform.git",
			Apps: []tektondagv1alpha1.StackApp{
				{Name: "demo-fe", Repo: "example/demo-fe", Role: "frontend"},
			},
		},
	}
	if err := testClient.Create(ctx, stack); err != nil {
		t.Fatal(err)
	}

	reconciler := &controller.StackRunReconciler{
		Client: testClient,
		Scheme: testScheme,
	}
	requestFor := func(name string) ctrl.Request {
		return ctrl.Request{NamespacedName: types.NamespacedName{
			Name: name, Namespace: namespace.Name,
		}}
	}

	t.Run("creation status and idempotency", func(t *testing.T) {
		run := &tektondagv1alpha1.StackRun{
			ObjectMeta: metav1.ObjectMeta{Name: "bootstrap-domain", Namespace: namespace.Name},
			Spec: tektondagv1alpha1.StackRunSpec{
				Mode:     tektondagv1alpha1.StackRunModeBootstrap,
				StackRef: "stack-one",
			},
		}
		if err := testClient.Create(ctx, run); err != nil {
			t.Fatal(err)
		}
		if _, err := reconciler.Reconcile(ctx, requestFor(run.Name)); err != nil {
			t.Fatal(err)
		}

		got := &tektondagv1alpha1.StackRun{}
		if err := testClient.Get(ctx, client.ObjectKeyFromObject(run), got); err != nil {
			t.Fatal(err)
		}
		if got.Status.PipelineRunName != run.Name || got.Status.Phase != "Pending" {
			t.Fatalf("unexpected StackRun status: %#v", got.Status)
		}

		pr := pipelineRun(run.Name, namespace.Name)
		if err := testClient.Get(ctx, client.ObjectKeyFromObject(run), pr); err != nil {
			t.Fatal(err)
		}
		if ref, _, _ := unstructured.NestedString(pr.Object, "spec", "pipelineRef", "name"); ref != "stack-bootstrap" {
			t.Fatalf("pipelineRef=%q", ref)
		}

		if _, err := reconciler.Reconcile(ctx, requestFor(run.Name)); err != nil {
			t.Fatal(err)
		}
		list := &unstructured.UnstructuredList{}
		list.SetGroupVersionKind(schema.GroupVersionKind{
			Group: "tekton.dev", Version: "v1", Kind: "PipelineRunList",
		})
		if err := testClient.List(ctx, list, client.InNamespace(namespace.Name)); err != nil {
			t.Fatal(err)
		}
		if len(list.Items) != 1 {
			t.Fatalf("reconcile created %d PipelineRuns, want 1", len(list.Items))
		}

		if err := unstructured.SetNestedSlice(pr.Object, []any{
			map[string]any{"type": "Succeeded", "status": "True", "reason": "Succeeded"},
		}, "status", "conditions"); err != nil {
			t.Fatal(err)
		}
		if err := testClient.Status().Update(ctx, pr); err != nil {
			t.Fatal(err)
		}
		if _, err := reconciler.Reconcile(ctx, requestFor(run.Name)); err != nil {
			t.Fatal(err)
		}
		if err := testClient.Get(ctx, client.ObjectKeyFromObject(run), got); err != nil {
			t.Fatal(err)
		}
		if got.Status.Phase != "Succeeded" {
			t.Fatalf("phase=%q, want Succeeded", got.Status.Phase)
		}
	})

	t.Run("approval blocks then creates", func(t *testing.T) {
		run := &tektondagv1alpha1.StackRun{
			ObjectMeta: metav1.ObjectMeta{Name: "promote-domain", Namespace: namespace.Name},
			Spec: tektondagv1alpha1.StackRunSpec{
				Mode:              tektondagv1alpha1.StackRunModePromote,
				StackRef:          "stack-one",
				ChangedApp:        "demo-fe",
				ReleaseVersion:    "1.2.3",
				TargetEnvironment: "staging",
				RequireApproval:   true,
			},
		}
		if err := testClient.Create(ctx, run); err != nil {
			t.Fatal(err)
		}
		if _, err := reconciler.Reconcile(ctx, requestFor(run.Name)); err != nil {
			t.Fatal(err)
		}
		got := &tektondagv1alpha1.StackRun{}
		if err := testClient.Get(ctx, client.ObjectKeyFromObject(run), got); err != nil {
			t.Fatal(err)
		}
		if got.Status.Phase != "PendingApproval" {
			t.Fatalf("phase=%q", got.Status.Phase)
		}
		if err := testClient.Get(ctx, client.ObjectKeyFromObject(run), pipelineRun(run.Name, namespace.Name)); err == nil {
			t.Fatal("PipelineRun exists before approval")
		}

		got.Spec.ApprovedBy = "integration-test"
		if err := testClient.Update(ctx, got); err != nil {
			t.Fatal(err)
		}
		if _, err := reconciler.Reconcile(ctx, requestFor(run.Name)); err != nil {
			t.Fatal(err)
		}
		if err := testClient.Get(ctx, client.ObjectKeyFromObject(run), pipelineRun(run.Name, namespace.Name)); err != nil {
			t.Fatal(err)
		}
	})

	t.Run("continuation carries results and pvc", func(t *testing.T) {
		sourcePR := pipelineRun("source-pr", namespace.Name)
		sourcePR.Object["spec"] = map[string]any{"params": []any{
			map[string]any{"name": "git-url", "value": "https://github.com/example/platform.git"},
			map[string]any{"name": "git-revision", "value": "main"},
			map[string]any{"name": "changed-app", "value": "demo-fe"},
		}}
		if err := testClient.Create(ctx, sourcePR); err != nil {
			t.Fatal(err)
		}
		sourceTR := taskRun("source-task", namespace.Name)
		sourceTR.SetLabels(map[string]string{"tekton.dev/pipelineRun": sourcePR.GetName()})
		sourceTR.Object["spec"] = map[string]any{"workspaces": []any{
			map[string]any{
				"name":                  "shared-workspace",
				"persistentVolumeClaim": map[string]any{"claimName": "source-pvc"},
			},
		}}
		if err := testClient.Create(ctx, sourceTR); err != nil {
			t.Fatal(err)
		}
		if err := unstructured.SetNestedSlice(sourceTR.Object, []any{
			map[string]any{"name": "stack-json", "value": `{"apps":[]}`},
			map[string]any{"name": "built-images", "value": `{"demo-fe":"image:v1"}`},
		}, "status", "results"); err != nil {
			t.Fatal(err)
		}
		if err := testClient.Status().Update(ctx, sourceTR); err != nil {
			t.Fatal(err)
		}

		run := &tektondagv1alpha1.StackRun{
			ObjectMeta: metav1.ObjectMeta{Name: "continue-domain", Namespace: namespace.Name},
			Spec: tektondagv1alpha1.StackRunSpec{
				Mode:         tektondagv1alpha1.StackRunModePR,
				ContinueFrom: sourcePR.GetName(),
			},
		}
		if err := testClient.Create(ctx, run); err != nil {
			t.Fatal(err)
		}
		if _, err := reconciler.Reconcile(ctx, requestFor(run.Name)); err != nil {
			t.Fatal(err)
		}
		pr := pipelineRun(run.Name, namespace.Name)
		if err := testClient.Get(ctx, client.ObjectKeyFromObject(run), pr); err != nil {
			t.Fatal(err)
		}
		ref, _, _ := unstructured.NestedString(pr.Object, "spec", "pipelineRef", "name")
		if ref != "stack-pr-continue" {
			t.Fatalf("pipelineRef=%q", ref)
		}
		workspaces, _, _ := unstructured.NestedSlice(pr.Object, "spec", "workspaces")
		pvc, _, _ := unstructured.NestedString(
			workspaces[0].(map[string]any),
			"persistentVolumeClaim",
			"claimName",
		)
		if pvc != "source-pvc" {
			t.Fatalf("workspace PVC=%q", pvc)
		}
	})
}

func TestInvalidStackRejectedByCRDSchema(t *testing.T) {
	ctx := context.Background()
	namespace := &corev1.Namespace{ObjectMeta: metav1.ObjectMeta{GenerateName: "invalid-stack-"}}
	if err := testClient.Create(ctx, namespace); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = testClient.Delete(ctx, namespace) })

	invalid := &tektondagv1alpha1.Stack{
		ObjectMeta: metav1.ObjectMeta{Name: "invalid", Namespace: namespace.Name},
		Spec: tektondagv1alpha1.StackSpec{
			Name: "invalid",
			Apps: nil,
		},
	}
	if err := testClient.Create(ctx, invalid); err == nil {
		t.Fatal("invalid Stack with no apps was admitted")
	}
}

func pipelineRun(name, namespace string) *unstructured.Unstructured {
	obj := &unstructured.Unstructured{}
	obj.SetGroupVersionKind(pipeline.PipelineRunGVK)
	obj.SetName(name)
	obj.SetNamespace(namespace)
	return obj
}

func taskRun(name, namespace string) *unstructured.Unstructured {
	obj := &unstructured.Unstructured{}
	obj.SetGroupVersionKind(schema.GroupVersionKind{
		Group: "tekton.dev", Version: "v1", Kind: "TaskRun",
	})
	obj.SetName(name)
	obj.SetNamespace(namespace)
	return obj
}
