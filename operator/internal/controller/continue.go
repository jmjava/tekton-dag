package controller

import (
	"context"
	"fmt"

	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
	"github.com/jmjava/tekton-dag/operator/internal/pipeline"
)

func (r *StackRunReconciler) fillContinue(ctx context.Context, run *tektondagv1alpha1.StackRun, opt *pipeline.Options) error {
	ns := pipelineNamespace(run)
	src := opt.ContinueFrom
	prName := src
	var sr tektondagv1alpha1.StackRun
	if err := r.Get(ctx, types.NamespacedName{Name: src, Namespace: run.Namespace}, &sr); err == nil {
		if sr.Status.PipelineRunName != "" {
			prName = sr.Status.PipelineRunName
		}
	} else if !apierrors.IsNotFound(err) {
		return err
	}
	pr := &unstructured.Unstructured{}
	pr.SetGroupVersionKind(pipeline.PipelineRunGVK)
	if err := r.Get(ctx, types.NamespacedName{Name: prName, Namespace: ns}, pr); err != nil {
		return fmt.Errorf("continueFrom %q: %w", src, err)
	}
	if v := pipelineParam(pr, "git-url"); v != "" && opt.GitURL == "" {
		opt.GitURL = v
	}
	if v := pipelineParam(pr, "git-revision"); v != "" && opt.GitRevision == "" {
		opt.GitRevision = v
	}
	if v := pipelineParam(pr, "changed-app"); v != "" && opt.ChangedApp == "" {
		opt.ChangedApp = v
	}
	if v := pipelineParam(pr, "intercept-backend"); v != "" && opt.InterceptBackend == "" {
		opt.InterceptBackend = v
	}

	list := &unstructured.UnstructuredList{}
	list.SetGroupVersionKind(pipeline.TaskRunListGVK)
	if err := r.List(ctx, list, client.InNamespace(ns), client.MatchingLabels{"tekton.dev/pipelineRun": prName}); err != nil {
		return err
	}
	results := map[string]string{}
	pvc := ""
	for i := range list.Items {
		tr := &list.Items[i]
		mergeTaskResults(tr, results)
		if pvc == "" {
			pvc = workspacePVC(tr)
		}
	}
	if pvc == "" {
		return fmt.Errorf("continueFrom %q: workspace PVC not found on TaskRuns", src)
	}
	opt.WorkspacePVC = pvc
	opt.ContinueStackJSON = results["stack-json"]
	opt.ContinueBuildApps = results["build-apps"]
	opt.ContinueChain = results["propagation-chain"]
	opt.ContinueHeader = results["intercept-header-value"]
	opt.ContinueAppList = results["app-list"]
	opt.ContinueEntryApp = results["entry-app"]
	opt.ContinueImages = results["built-images"]
	opt.ContinueVersions = results["bumped-versions"]
	if opt.ContinueStackJSON == "" || opt.ContinueImages == "" {
		return fmt.Errorf("continueFrom %q: resolve-stack/build-apps results missing", src)
	}
	return nil
}

func pipelineParam(pr *unstructured.Unstructured, name string) string {
	params, found, _ := unstructured.NestedSlice(pr.Object, "spec", "params")
	if !found {
		return ""
	}
	for _, p := range params {
		m, ok := p.(map[string]any)
		if !ok {
			continue
		}
		if m["name"] == name {
			if s, ok := m["value"].(string); ok {
				return s
			}
		}
	}
	return ""
}

func mergeTaskResults(tr *unstructured.Unstructured, out map[string]string) {
	raw, found, _ := unstructured.NestedSlice(tr.Object, "status", "results")
	if !found {
		return
	}
	for _, r := range raw {
		m, ok := r.(map[string]any)
		if !ok {
			continue
		}
		name, _ := m["name"].(string)
		val, _ := m["value"].(string)
		if name != "" && val != "" {
			out[name] = val
		}
	}
}

func workspacePVC(tr *unstructured.Unstructured) string {
	wss, found, _ := unstructured.NestedSlice(tr.Object, "spec", "workspaces")
	if !found {
		return ""
	}
	for _, w := range wss {
		m, ok := w.(map[string]any)
		if !ok {
			continue
		}
		name, _ := m["name"].(string)
		if name != "source" && name != "output" && name != "shared-workspace" {
			continue
		}
		claim, _, _ := unstructured.NestedString(m, "persistentVolumeClaim", "claimName")
		if claim != "" {
			return claim
		}
	}
	return ""
}
