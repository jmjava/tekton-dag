// Package pipeline builds Tekton PipelineRun unstructured objects.
// Contract matches orchestrator/pipelinerun_builder.py + tekton_dag_common.reliability.
package pipeline

import (
	"crypto/rand"
	"encoding/json"
	"fmt"
	"math/big"
	"strconv"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
)

const (
	TektonAPIVersion   = "tekton.dev/v1"
	StandardPartOf     = "tekton-job-standardization"
	DefaultTimeout     = "2h"
	DefaultMaxRetries  = 2
	DefaultServiceAcct = "tekton-pr-sa"
)

var PipelineRunGVK = schema.GroupVersionKind{
	Group:   "tekton.dev",
	Version: "v1",
	Kind:    "PipelineRun",
}

// Options for building PipelineRuns.
type Options struct {
	NameSuffix         string // when set, used instead of random suffix (tests)
	Namespace          string
	StackFile          string
	GitURL             string
	GitRevision        string
	ImageRegistry      string
	CacheRepo          string
	ChangedApp         string
	PRNumber           int
	AppRevisions       string
	InterceptBackend   string
	DashboardURL       string
	PRRepoURL          string
	CompileImages      map[string]string
	ReleaseVersion     string
	TargetEnvironment  string
	TargetRegistry     string
	CredentialsSecret  string
	RequireApproval    bool
	ApprovedBy         string
	Timeout            string
	MaxRetries         *int
	ServiceAccountName string
	// Platform-upgrade
	ActiveSlot   string
	TargetSlot   string
	GateTaskRefs []string
	GateRegistry string
}

func randomSuffix(length int) string {
	const alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
	out := make([]byte, length)
	for i := range out {
		n, err := rand.Int(rand.Reader, big.NewInt(int64(len(alphabet))))
		if err != nil {
			out[i] = alphabet[i%len(alphabet)]
			continue
		}
		out[i] = alphabet[n.Int64()]
	}
	return string(out)
}

func suffix(opt Options) string {
	if opt.NameSuffix != "" {
		return opt.NameSuffix
	}
	return randomSuffix(5)
}

func sa(opt Options) string {
	if opt.ServiceAccountName != "" {
		return opt.ServiceAccountName
	}
	return DefaultServiceAcct
}

func ns(opt Options) string {
	if opt.Namespace != "" {
		return opt.Namespace
	}
	return "tekton-pipelines"
}

func timeout(opt Options) string {
	if opt.Timeout != "" {
		return opt.Timeout
	}
	return DefaultTimeout
}

func maxRetries(opt Options) int {
	if opt.MaxRetries != nil {
		return *opt.MaxRetries
	}
	return DefaultMaxRetries
}

func param(name, value string) map[string]any {
	return map[string]any{"name": name, "value": value}
}

func defaultWorkspaces(storage string) []any {
	return []any{
		map[string]any{
			"name": "shared-workspace",
			"volumeClaimTemplate": map[string]any{
				"spec": map[string]any{
					"accessModes": []any{"ReadWriteOnce"},
					"resources": map[string]any{
						"requests": map[string]any{"storage": storage},
					},
				},
			},
		},
		map[string]any{
			"name": "ssh-key",
			"secret": map[string]any{
				"secretName": "ssh-key-secret",
			},
		},
		map[string]any{
			"name": "build-cache",
			"persistentVolumeClaim": map[string]any{
				"claimName": "build-cache-pvc",
			},
		},
	}
}

func applyReliability(obj map[string]any, opt Options) {
	spec := obj["spec"].(map[string]any)
	spec["timeouts"] = map[string]any{"pipeline": timeout(opt)}
	params := spec["params"].([]any)
	filtered := make([]any, 0, len(params)+1)
	for _, p := range params {
		m := p.(map[string]any)
		if m["name"] == "max-retries" {
			continue
		}
		filtered = append(filtered, p)
	}
	filtered = append(filtered, param("max-retries", strconv.Itoa(maxRetries(opt))))
	spec["params"] = filtered
}

func appendCompileImages(params *[]any, images map[string]string, keys [][2]string) {
	for _, pair := range keys {
		key, paramName := pair[0], pair[1]
		if v, ok := images[key]; ok && v != "" {
			*params = append(*params, param(paramName, v))
		}
	}
}

func toUnstructured(obj map[string]any) (*unstructured.Unstructured, error) {
	u := &unstructured.Unstructured{Object: obj}
	u.SetGroupVersionKind(PipelineRunGVK)
	return u, nil
}

// BuildPR builds a stack-pr-test PipelineRun.
func BuildPR(opt Options) (*unstructured.Unstructured, error) {
	name := fmt.Sprintf("stack-pr-%d-%s", opt.PRNumber, suffix(opt))
	appRev := opt.AppRevisions
	if appRev == "" {
		appRev = "{}"
	}
	intercept := opt.InterceptBackend
	if intercept == "" {
		intercept = "telepresence"
	}
	params := []any{
		param("git-url", opt.GitURL),
		param("git-revision", opt.GitRevision),
		param("stack-file", opt.StackFile),
		param("changed-app", opt.ChangedApp),
		param("pr-number", strconv.Itoa(opt.PRNumber)),
		param("app-revisions", appRev),
		param("image-registry", opt.ImageRegistry),
		param("cache-repo", opt.CacheRepo),
		param("intercept-backend", intercept),
		param("dashboard-url", opt.DashboardURL),
		param("pr-repo-url", opt.PRRepoURL),
	}
	appendCompileImages(&params, opt.CompileImages, [][2]string{
		{"npm", "compile-image-npm"},
		{"maven", "compile-image-maven"},
		{"gradle", "compile-image-gradle"},
		{"pip", "compile-image-pip"},
		{"php", "compile-image-php"},
		{"mirrord", "compile-image-mirrord"},
	})
	obj := map[string]any{
		"apiVersion": TektonAPIVersion,
		"kind":       "PipelineRun",
		"metadata": map[string]any{
			"name":      name,
			"namespace": ns(opt),
			"labels": map[string]any{
				"tekton.dev/pipeline":          "stack-pr-test",
				"app.kubernetes.io/part-of":    StandardPartOf,
			},
		},
		"spec": map[string]any{
			"pipelineRef": map[string]any{"name": "stack-pr-test"},
			"params":      params,
			"workspaces":  defaultWorkspaces("2Gi"),
			"taskRunTemplate": map[string]any{
				"serviceAccountName": sa(opt),
			},
		},
	}
	applyReliability(obj, opt)
	return toUnstructured(obj)
}

// BuildBootstrap builds a stack-bootstrap PipelineRun.
func BuildBootstrap(opt Options) (*unstructured.Unstructured, error) {
	name := fmt.Sprintf("stack-bootstrap-%s", suffix(opt))
	params := []any{
		param("git-url", opt.GitURL),
		param("git-revision", opt.GitRevision),
		param("stack-file", opt.StackFile),
		param("image-registry", opt.ImageRegistry),
		param("cache-repo", opt.CacheRepo),
	}
	appendCompileImages(&params, opt.CompileImages, [][2]string{
		{"npm", "compile-image-npm"},
		{"maven", "compile-image-maven"},
		{"gradle", "compile-image-gradle"},
		{"pip", "compile-image-pip"},
		{"php", "compile-image-php"},
	})
	obj := map[string]any{
		"apiVersion": TektonAPIVersion,
		"kind":       "PipelineRun",
		"metadata": map[string]any{
			"name":      name,
			"namespace": ns(opt),
			"labels": map[string]any{
				"tekton.dev/pipeline":          "stack-bootstrap",
				"app.kubernetes.io/part-of":    StandardPartOf,
			},
		},
		"spec": map[string]any{
			"pipelineRef": map[string]any{"name": "stack-bootstrap"},
			"params":      params,
			"workspaces":  defaultWorkspaces("2Gi"),
			"taskRunTemplate": map[string]any{
				"serviceAccountName": sa(opt),
			},
		},
	}
	applyReliability(obj, opt)
	return toUnstructured(obj)
}

// BuildMerge builds a stack-merge-release PipelineRun.
func BuildMerge(opt Options) (*unstructured.Unstructured, error) {
	name := fmt.Sprintf("stack-merge-%s", suffix(opt))
	params := []any{
		param("git-url", opt.GitURL),
		param("git-revision", opt.GitRevision),
		param("stack-file", opt.StackFile),
		param("changed-app", opt.ChangedApp),
		param("image-registry", opt.ImageRegistry),
		param("cache-repo", opt.CacheRepo),
	}
	obj := map[string]any{
		"apiVersion": TektonAPIVersion,
		"kind":       "PipelineRun",
		"metadata": map[string]any{
			"name":      name,
			"namespace": ns(opt),
			"labels": map[string]any{
				"tekton.dev/pipeline":          "stack-merge-release",
				"app.kubernetes.io/part-of":    StandardPartOf,
			},
		},
		"spec": map[string]any{
			"pipelineRef": map[string]any{"name": "stack-merge-release"},
			"params":      params,
			"workspaces":  defaultWorkspaces("2Gi"),
			"taskRunTemplate": map[string]any{
				"serviceAccountName": sa(opt),
			},
		},
	}
	applyReliability(obj, opt)
	return toUnstructured(obj)
}

// BuildPromote builds a stack-promote PipelineRun.
func BuildPromote(opt Options) (*unstructured.Unstructured, error) {
	name := fmt.Sprintf("stack-promote-%s-%s", opt.TargetEnvironment, suffix(opt))
	workspaces := []any{
		map[string]any{
			"name": "shared-workspace",
			"volumeClaimTemplate": map[string]any{
				"spec": map[string]any{
					"accessModes": []any{"ReadWriteOnce"},
					"resources": map[string]any{
						"requests": map[string]any{"storage": "1Gi"},
					},
				},
			},
		},
	}
	if opt.CredentialsSecret != "" {
		workspaces = append(workspaces, map[string]any{
			"name": "dockerconfig",
			"secret": map[string]any{
				"secretName": opt.CredentialsSecret,
				"items": []any{
					map[string]any{"key": ".dockerconfigjson", "path": "config.json"},
				},
			},
		})
	}
	requireApproval := "false"
	if opt.RequireApproval {
		requireApproval = "true"
	}
	params := []any{
		param("stack-file", opt.StackFile),
		param("release-version", opt.ReleaseVersion),
		param("target-environment", opt.TargetEnvironment),
		param("image-registry", opt.ImageRegistry),
		param("target-registry", opt.TargetRegistry),
		param("credentials-secret", opt.CredentialsSecret),
		param("changed-app", opt.ChangedApp),
		param("apps", opt.ChangedApp),
	}
	obj := map[string]any{
		"apiVersion": TektonAPIVersion,
		"kind":       "PipelineRun",
		"metadata": map[string]any{
			"name":      name,
			"namespace": ns(opt),
			"labels": map[string]any{
				"tekton.dev/pipeline":          "stack-promote",
				"app.kubernetes.io/part-of":    StandardPartOf,
				"tekton-dag.io/environment":    opt.TargetEnvironment,
			},
			"annotations": map[string]any{
				"tekton-dag.io/release-version":  opt.ReleaseVersion,
				"tekton-dag.io/approved-by":      opt.ApprovedBy,
				"tekton-dag.io/require-approval": requireApproval,
				"tekton-dag.io/max-retries-note": "PipelineRun param max-retries is for audit; Tekton task retries on promote remain fixed at 2",
			},
		},
		"spec": map[string]any{
			"pipelineRef": map[string]any{"name": "stack-promote"},
			"params":      params,
			"workspaces":  workspaces,
			"taskRunTemplate": map[string]any{
				"serviceAccountName": sa(opt),
			},
		},
	}
	applyReliability(obj, opt)
	return toUnstructured(obj)
}

// BuildPlatformUpgrade builds a platform-upgrade PipelineRun.
//
// Composition is warm → gates → cutover via pipelineRef "platform-upgrade".
// Gate Task names are params only — no Volcano/Chaos/Trivy knowledge in-core.
func BuildPlatformUpgrade(opt Options) (*unstructured.Unstructured, error) {
	name := fmt.Sprintf("platform-upgrade-%s-%s", opt.ReleaseVersion, suffix(opt))
	gates := opt.GateTaskRefs
	if gates == nil {
		gates = []string{}
	}
	gatesJSON, err := json.Marshal(gates)
	if err != nil {
		return nil, err
	}
	active := opt.ActiveSlot
	if active == "" {
		active = "blue"
	}
	target := opt.TargetSlot
	if target == "" {
		target = "green"
	}
	params := []any{
		param("release-version", opt.ReleaseVersion),
		param("active-slot", active),
		param("target-slot", target),
		param("gate-task-refs", string(gatesJSON)),
		param("gate-registry", opt.GateRegistry),
		param("image-registry", opt.ImageRegistry),
	}
	obj := map[string]any{
		"apiVersion": TektonAPIVersion,
		"kind":       "PipelineRun",
		"metadata": map[string]any{
			"name":      name,
			"namespace": ns(opt),
			"labels": map[string]any{
				"tekton.dev/pipeline":       "platform-upgrade",
				"app.kubernetes.io/part-of": StandardPartOf,
				"tektondag.io/mode":         "platform-upgrade",
			},
			"annotations": map[string]any{
				"tekton-dag.io/release-version": opt.ReleaseVersion,
				"tekton-dag.io/active-slot":     active,
				"tekton-dag.io/target-slot":     target,
			},
		},
		"spec": map[string]any{
			"pipelineRef": map[string]any{"name": "platform-upgrade"},
			"params":      params,
			"workspaces":  defaultWorkspaces("1Gi"),
			"taskRunTemplate": map[string]any{
				"serviceAccountName": sa(opt),
			},
		},
	}
	applyReliability(obj, opt)
	return toUnstructured(obj)
}

// CanonicalJSON returns stable JSON for golden comparisons (sorted keys via encoding/json map encoding).
func CanonicalJSON(u *unstructured.Unstructured) ([]byte, error) {
	return json.MarshalIndent(u.Object, "", "  ")
}
