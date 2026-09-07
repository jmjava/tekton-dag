package controller

import (
	"testing"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

func TestMergeTaskResultsAndPVC(t *testing.T) {
	tr := &unstructured.Unstructured{Object: map[string]any{
		"spec": map[string]any{
			"workspaces": []any{
				map[string]any{
					"name": "shared-workspace",
					"persistentVolumeClaim": map[string]any{
						"claimName": "pvc-from-failed",
					},
				},
			},
		},
		"status": map[string]any{
			"results": []any{
				map[string]any{"name": "stack-json", "value": `{"apps":[]}`},
				map[string]any{"name": "built-images", "value": `{"fe":"img"}`},
			},
		},
	}}
	out := map[string]string{}
	mergeTaskResults(tr, out)
	if out["stack-json"] != `{"apps":[]}` || out["built-images"] != `{"fe":"img"}` {
		t.Fatalf("results=%v", out)
	}
	if got := workspacePVC(tr); got != "pvc-from-failed" {
		t.Fatalf("pvc=%q", got)
	}
}

func TestPipelineParam(t *testing.T) {
	pr := &unstructured.Unstructured{Object: map[string]any{
		"spec": map[string]any{
			"params": []any{
				map[string]any{"name": "git-url", "value": "https://example.com/r.git"},
				map[string]any{"name": "changed-app", "value": "demo-fe"},
			},
		},
	}}
	if pipelineParam(pr, "git-url") != "https://example.com/r.git" {
		t.Fatal("git-url")
	}
	if pipelineParam(pr, "missing") != "" {
		t.Fatal("missing should be empty")
	}
}
