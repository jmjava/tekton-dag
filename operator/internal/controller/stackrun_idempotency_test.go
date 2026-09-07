package controller

import (
	"context"
	"testing"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"

	"github.com/jmjava/tekton-dag/operator/internal/pipeline"
)

func testScheme(t *testing.T) *runtime.Scheme {
	t.Helper()
	s := runtime.NewScheme()
	if err := tektondagv1alpha1.AddToScheme(s); err != nil {
		t.Fatal(err)
	}
	return s
}

func sampleStack(ns string) *tektondagv1alpha1.Stack {
	return &tektondagv1alpha1.Stack{
		ObjectMeta: metav1.ObjectMeta{Name: "stack-one", Namespace: ns},
		Spec: tektondagv1alpha1.StackSpec{
			Name:      "stack-one",
			StackFile: "stacks/stack-one.yaml",
			GitURL:    "https://github.com/jmjava/tekton-dag.git",
			Apps: []tektondagv1alpha1.StackApp{
				{Name: "demo-fe", Repo: "jmjava/tekton-dag-demo-fe"},
			},
		},
	}
}

func TestOptionsFromStackRunReadsPRAnnotation(t *testing.T) {
	ns := "tekton-pipelines"
	s := testScheme(t)
	cl := fake.NewClientBuilder().WithScheme(s).WithObjects(sampleStack(ns)).Build()
	r := &StackRunReconciler{Client: cl, Scheme: s}
	run := &tektondagv1alpha1.StackRun{
		ObjectMeta: metav1.ObjectMeta{
			Name:        "stackrun-pr-abc",
			Namespace:   ns,
			Annotations: map[string]string{"tektondag.io/pr-number": "42"},
		},
		Spec: tektondagv1alpha1.StackRunSpec{
			Mode:       tektondagv1alpha1.StackRunModePR,
			ChangedApp: "demo-fe",
		},
	}
	opt, err := r.optionsFromStackRun(context.Background(), run)
	if err != nil {
		t.Fatal(err)
	}
	if opt.PRNumber != 42 {
		t.Fatalf("PRNumber=%d want 42 from annotation", opt.PRNumber)
	}
	if opt.StackFile != "stacks/stack-one.yaml" {
		t.Fatalf("StackFile=%q", opt.StackFile)
	}
	if run.Spec.StackRef != "" {
		t.Fatalf("must not mutate spec.stackRef, got %q", run.Spec.StackRef)
	}
}

func TestLookupStackByRepoShort(t *testing.T) {
	ns := "tekton-pipelines"
	s := testScheme(t)
	cl := fake.NewClientBuilder().WithScheme(s).WithObjects(sampleStack(ns)).Build()
	r := &StackRunReconciler{Client: cl, Scheme: s}
	run := &tektondagv1alpha1.StackRun{
		ObjectMeta: metav1.ObjectMeta{Name: "sr", Namespace: ns},
		Spec: tektondagv1alpha1.StackRunSpec{
			Mode:       tektondagv1alpha1.StackRunModeMerge,
			ChangedApp: "tekton-dag-demo-fe",
		},
	}
	st, app, err := r.lookupStack(context.Background(), run)
	if err != nil {
		t.Fatal(err)
	}
	if st == nil || st.Name != "stack-one" {
		t.Fatalf("stack=%v", st)
	}
	if app != "demo-fe" {
		t.Fatalf("app=%q want demo-fe", app)
	}
}

func TestFindExistingPipelineRunByNameAndLabel(t *testing.T) {
	ns := "tekton-pipelines"
	s := testScheme(t)
	named := &unstructured.Unstructured{Object: map[string]any{
		"apiVersion": "tekton.dev/v1",
		"kind":       "PipelineRun",
		"metadata": map[string]any{
			"name":      "stackrun-bootstrap-x",
			"namespace": ns,
			"labels":    map[string]any{labelStackRun: "stackrun-bootstrap-x"},
		},
	}}
	named.SetGroupVersionKind(pipeline.PipelineRunGVK)
	labeled := &unstructured.Unstructured{Object: map[string]any{
		"apiVersion": "tekton.dev/v1",
		"kind":       "PipelineRun",
		"metadata": map[string]any{
			"name":      "old-random-name",
			"namespace": ns,
			"labels":    map[string]any{labelStackRun: "stackrun-legacy"},
		},
	}}
	labeled.SetGroupVersionKind(pipeline.PipelineRunGVK)

	cl := fake.NewClientBuilder().WithScheme(s).WithObjects(named, labeled).Build()
	r := &StackRunReconciler{Client: cl, Scheme: s}

	got, err := r.findExistingPipelineRun(context.Background(), &tektondagv1alpha1.StackRun{
		ObjectMeta: metav1.ObjectMeta{Name: "stackrun-bootstrap-x", Namespace: ns},
	})
	if err != nil {
		t.Fatal(err)
	}
	if got != "stackrun-bootstrap-x" {
		t.Fatalf("got %q want stackrun-bootstrap-x", got)
	}

	got, err = r.findExistingPipelineRun(context.Background(), &tektondagv1alpha1.StackRun{
		ObjectMeta: metav1.ObjectMeta{Name: "stackrun-legacy", Namespace: ns},
	})
	if err != nil {
		t.Fatal(err)
	}
	if got != "old-random-name" {
		t.Fatalf("got %q want old-random-name (label adopt)", got)
	}

	got, err = r.findExistingPipelineRun(context.Background(), &tektondagv1alpha1.StackRun{
		ObjectMeta: metav1.ObjectMeta{Name: "missing", Namespace: ns},
	})
	if err != nil {
		t.Fatal(err)
	}
	if got != "" {
		t.Fatalf("expected empty, got %q", got)
	}
}

func TestMapPipelineRunToStackRun(t *testing.T) {
	pr := &unstructured.Unstructured{}
	pr.SetNamespace("tekton-pipelines")
	pr.SetLabels(map[string]string{labelStackRun: "sr-1"})
	reqs := mapPipelineRunToStackRun(context.Background(), pr)
	if len(reqs) != 1 || reqs[0].Name != "sr-1" || reqs[0].Namespace != "tekton-pipelines" {
		t.Fatalf("reqs=%v", reqs)
	}
	if reqs := mapPipelineRunToStackRun(context.Background(), &unstructured.Unstructured{}); len(reqs) != 0 {
		t.Fatalf("unlabeled should be empty")
	}
}

func TestFindExistingIgnoresOtherNamespace(t *testing.T) {
	s := testScheme(t)
	pr := &unstructured.Unstructured{Object: map[string]any{
		"apiVersion": "tekton.dev/v1",
		"kind":       "PipelineRun",
		"metadata": map[string]any{
			"name":      "stackrun-x",
			"namespace": "other",
		},
	}}
	pr.SetGroupVersionKind(pipeline.PipelineRunGVK)
	cl := fake.NewClientBuilder().WithScheme(s).WithObjects(pr).Build()
	r := &StackRunReconciler{Client: cl, Scheme: s}
	got, err := r.findExistingPipelineRun(context.Background(), &tektondagv1alpha1.StackRun{
		ObjectMeta: metav1.ObjectMeta{Name: "stackrun-x", Namespace: "tekton-pipelines"},
	})
	if err != nil {
		t.Fatal(err)
	}
	if got != "" {
		t.Fatalf("must not adopt other-namespace PR, got %q", got)
	}
}
