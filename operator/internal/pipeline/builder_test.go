package pipeline

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

func mr(v int) *int { return &v }

func TestBuildersMatchGolden(t *testing.T) {
	fixtures := filepath.Join("testdata", "golden")

	optBase := Options{
		NameSuffix:    "fixed",
		Namespace:     "tekton-pipelines",
		StackFile:     "stacks/stack-one.yaml",
		GitURL:        "https://github.com/jmjava/tekton-dag.git",
		GitRevision:   "main",
		ImageRegistry: "localhost:5000",
		CacheRepo:     "localhost:5000/kaniko-cache",
		Timeout:       "2h",
		MaxRetries:    mr(2),
	}

	prOpt := optBase
	prOpt.ChangedApp = "demo-fe"
	prOpt.PRNumber = 42
	prOpt.AppRevisions = `{"demo-fe":"abc123"}`
	prOpt.InterceptBackend = "telepresence"

	mergeOpt := optBase
	mergeOpt.ChangedApp = "demo-fe"

	promoteOpt := optBase
	promoteOpt.ChangedApp = "demo-fe"
	promoteOpt.ReleaseVersion = "0.1.0"
	promoteOpt.TargetEnvironment = "staging"
	promoteOpt.TargetRegistry = "ghcr.io/example"
	promoteOpt.CredentialsSecret = "regcred"
	promoteOpt.RequireApproval = true
	promoteOpt.ApprovedBy = "alice"

	tests := []struct {
		file  string
		build func() (map[string]any, error)
	}{
		{"pr.json", func() (map[string]any, error) {
			u, err := BuildPR(prOpt)
			if err != nil {
				return nil, err
			}
			return u.Object, nil
		}},
		{"bootstrap.json", func() (map[string]any, error) {
			u, err := BuildBootstrap(optBase)
			if err != nil {
				return nil, err
			}
			return u.Object, nil
		}},
		{"merge.json", func() (map[string]any, error) {
			u, err := BuildMerge(mergeOpt)
			if err != nil {
				return nil, err
			}
			return u.Object, nil
		}},
		{"promote.json", func() (map[string]any, error) {
			u, err := BuildPromote(promoteOpt)
			if err != nil {
				return nil, err
			}
			return u.Object, nil
		}},
	}

	for _, tt := range tests {
		t.Run(tt.file, func(t *testing.T) {
			got, err := tt.build()
			if err != nil {
				t.Fatal(err)
			}
			gotJSON, err := json.Marshal(got)
			if err != nil {
				t.Fatal(err)
			}
			path := filepath.Join(fixtures, tt.file)
			wantBytes, err := os.ReadFile(path)
			if err != nil {
				t.Fatalf("read golden %s: %v (run scripts/generate-pipelinerun-goldens.py)", path, err)
			}
			var want, gotNorm any
			if err := json.Unmarshal(wantBytes, &want); err != nil {
				t.Fatal(err)
			}
			if err := json.Unmarshal(gotJSON, &gotNorm); err != nil {
				t.Fatal(err)
			}
			wantCanon, _ := json.Marshal(want)
			gotCanon, _ := json.Marshal(gotNorm)
			if string(wantCanon) != string(gotCanon) {
				t.Fatalf("mismatch for %s\nwant: %s\ngot:  %s", tt.file, wantCanon, gotCanon)
			}
		})
	}
}

func TestBuildPRContinue(t *testing.T) {
	opt := Options{
		NameSuffix:         "fixed",
		Namespace:          "tekton-pipelines",
		GitURL:             "https://github.com/jmjava/tekton-dag.git",
		GitRevision:        "main",
		ChangedApp:         "demo-fe",
		WorkspacePVC:       "ws-pvc",
		ContinueStackJSON:  `{"apps":[]}`,
		ContinueBuildApps:  "demo-fe",
		ContinueImages:     `{"demo-fe":"img"}`,
		ContinueFrom:       "stack-pr-1",
	}
	u, err := BuildPRContinue(opt)
	if err != nil {
		t.Fatal(err)
	}
	if u.GetName() != "stack-pr-continue-fixed" {
		t.Fatalf("name=%s", u.GetName())
	}
	ref, _, _ := unstructured.NestedString(u.Object, "spec", "pipelineRef", "name")
	if ref != "stack-pr-continue" {
		t.Fatalf("pipelineRef=%s", ref)
	}
}

