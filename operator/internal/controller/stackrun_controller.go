/*
Copyright 2026.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package controller

import (
	"context"
	"fmt"
	"strconv"

	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
	"github.com/jmjava/tekton-dag/operator/internal/pipeline"
)

const (
	// Label marking PipelineRuns owned by a StackRun. OwnerReference is set but
	// blockOwnerDeletion=false and we document orphan GC so Results history survives.
	labelStackRun = "tektondag.io/stackrun"
)

// StackRunReconciler creates Tekton PipelineRuns from StackRun specs.
type StackRunReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=tektondag.io,resources=stackruns,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=tektondag.io,resources=stackruns/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=tektondag.io,resources=stackruns/finalizers,verbs=update
// +kubebuilder:rbac:groups=tektondag.io,resources=stacks,verbs=get;list;watch
// +kubebuilder:rbac:groups=tekton.dev,resources=pipelineruns,verbs=get;list;watch;create;update;patch
// +kubebuilder:rbac:groups=tekton.dev,resources=taskruns,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=secrets,verbs=get;list

func (r *StackRunReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	var run tektondagv1alpha1.StackRun
	if err := r.Get(ctx, req.NamespacedName, &run); err != nil {
		if apierrors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, err
	}

	// Idempotent: if we already recorded a PipelineRun, sync status only.
	if run.Status.PipelineRunName != "" {
		return r.syncPipelineStatus(ctx, &run)
	}

	if waitingForApproval(&run) {
		return r.pendingApproval(ctx, &run)
	}

	opt, err := r.optionsFromStackRun(ctx, &run)
	if err != nil {
		return r.fail(ctx, &run, "InvalidSpec", err.Error())
	}

	pr, err := buildFromMode(run.Spec.Mode, opt)
	if err != nil {
		return r.fail(ctx, &run, "BuildFailed", err.Error())
	}

	// Annotate with StackRun identity; do NOT set controller OwnerReference that
	// cascades delete — orphan PipelineRuns so Tekton Results keep history.
	labels := pr.GetLabels()
	if labels == nil {
		labels = map[string]string{}
	}
	labels[labelStackRun] = run.Name
	pr.SetLabels(labels)
	ann := pr.GetAnnotations()
	if ann == nil {
		ann = map[string]string{}
	}
	ann["tektondag.io/stackrun-uid"] = string(run.UID)
	pr.SetAnnotations(ann)

	if err := r.Create(ctx, pr); err != nil {
		if apierrors.IsAlreadyExists(err) {
			// Rare name collision; record and sync.
		} else {
			logger.Error(err, "failed to create PipelineRun")
			return r.fail(ctx, &run, "CreateFailed", err.Error())
		}
	}

	run.Status.PipelineRunName = pr.GetName()
	run.Status.ObservedGeneration = run.Generation
	run.Status.Phase = "Pending"
	meta.SetStatusCondition(&run.Status.Conditions, metav1.Condition{
		Type:               "Ready",
		Status:             metav1.ConditionFalse,
		Reason:             "PipelineRunCreated",
		Message:            fmt.Sprintf("Created PipelineRun %s", pr.GetName()),
		ObservedGeneration: run.Generation,
	})
	if err := r.Status().Update(ctx, &run); err != nil {
		return ctrl.Result{}, err
	}
	return ctrl.Result{Requeue: true}, nil
}

func waitingForApproval(run *tektondagv1alpha1.StackRun) bool {
	return run.Spec.Mode == tektondagv1alpha1.StackRunModePromote &&
		run.Spec.RequireApproval &&
		run.Spec.ApprovedBy == ""
}

func (r *StackRunReconciler) pendingApproval(ctx context.Context, run *tektondagv1alpha1.StackRun) (ctrl.Result, error) {
	run.Status.ObservedGeneration = run.Generation
	run.Status.Phase = "PendingApproval"
	meta.SetStatusCondition(&run.Status.Conditions, metav1.Condition{
		Type:               "Ready",
		Status:             metav1.ConditionFalse,
		Reason:             "PendingApproval",
		Message:            "requireApproval is set; patch spec.approvedBy to create the PipelineRun",
		ObservedGeneration: run.Generation,
	})
	if err := r.Status().Update(ctx, run); err != nil {
		return ctrl.Result{}, err
	}
	return ctrl.Result{}, nil
}

func (r *StackRunReconciler) syncPipelineStatus(ctx context.Context, run *tektondagv1alpha1.StackRun) (ctrl.Result, error) {
	prNS := run.Spec.PipelineNamespace
	if prNS == "" {
		prNS = run.Namespace
	}
	pr := &unstructured.Unstructured{}
	pr.SetGroupVersionKind(pipeline.PipelineRunGVK)
	if err := r.Get(ctx, types.NamespacedName{Name: run.Status.PipelineRunName, Namespace: prNS}, pr); err != nil {
		if apierrors.IsNotFound(err) {
			return r.fail(ctx, run, "PipelineRunMissing", "PipelineRun not found (orphaned or deleted)")
		}
		return ctrl.Result{}, err
	}

	phase := "Unknown"
	conds, found, _ := unstructured.NestedSlice(pr.Object, "status", "conditions")
	if found && len(conds) > 0 {
		if c0, ok := conds[0].(map[string]any); ok {
			if reason, _ := c0["reason"].(string); reason != "" {
				phase = reason
			}
		}
	}
	run.Status.Phase = phase
	run.Status.ObservedGeneration = run.Generation
	ready := metav1.ConditionFalse
	reason := phase
	msg := fmt.Sprintf("PipelineRun %s phase=%s", run.Status.PipelineRunName, phase)
	if phase == "Succeeded" {
		ready = metav1.ConditionTrue
	}
	if phase == "Failed" || phase == "Cancelled" {
		reason = phase
	}
	meta.SetStatusCondition(&run.Status.Conditions, metav1.Condition{
		Type:               "Ready",
		Status:             ready,
		Reason:             reason,
		Message:            msg,
		ObservedGeneration: run.Generation,
	})
	if err := r.Status().Update(ctx, run); err != nil {
		return ctrl.Result{}, err
	}
	if phase == "Succeeded" || phase == "Failed" || phase == "Cancelled" {
		return ctrl.Result{}, nil
	}
	return ctrl.Result{Requeue: true}, nil
}

func (r *StackRunReconciler) fail(ctx context.Context, run *tektondagv1alpha1.StackRun, reason, msg string) (ctrl.Result, error) {
	run.Status.ObservedGeneration = run.Generation
	run.Status.Phase = "Error"
	meta.SetStatusCondition(&run.Status.Conditions, metav1.Condition{
		Type:               "Ready",
		Status:             metav1.ConditionFalse,
		Reason:             reason,
		Message:            msg,
		ObservedGeneration: run.Generation,
	})
	_ = r.Status().Update(ctx, run)
	return ctrl.Result{}, nil
}

func (r *StackRunReconciler) optionsFromStackRun(ctx context.Context, run *tektondagv1alpha1.StackRun) (pipeline.Options, error) {
	opt := pipeline.Options{
		Namespace:          run.Namespace,
		StackFile:          run.Spec.StackFile,
		GitURL:             run.Spec.GitURL,
		GitRevision:        run.Spec.GitRevision,
		ImageRegistry:      run.Spec.ImageRegistry,
		CacheRepo:          run.Spec.CacheRepo,
		ChangedApp:         run.Spec.ChangedApp,
		PRNumber:           int(run.Spec.PRNumber),
		AppRevisions:       run.Spec.AppRevisions,
		InterceptBackend:   run.Spec.InterceptBackend,
		DashboardURL:       run.Spec.DashboardURL,
		PRRepoURL:          run.Spec.PRRepoURL,
		ReleaseVersion:     run.Spec.ReleaseVersion,
		TargetEnvironment:  run.Spec.TargetEnvironment,
		TargetRegistry:     run.Spec.TargetRegistry,
		CredentialsSecret:  run.Spec.CredentialsSecret,
		RequireApproval:    run.Spec.RequireApproval,
		ApprovedBy:         run.Spec.ApprovedBy,
		Timeout:            run.Spec.Timeout,
		ServiceAccountName: run.Spec.ServiceAccountName,
	}
	if opt.PRNumber == 0 {
		if s := run.Annotations["tektondag.io/pr-number"]; s != "" {
			if n, err := strconv.Atoi(s); err == nil {
				opt.PRNumber = n
			}
		}
	}
	if run.Spec.PipelineNamespace != "" {
		opt.Namespace = run.Spec.PipelineNamespace
	}
	if run.Spec.MaxRetries != nil {
		v := int(*run.Spec.MaxRetries)
		opt.MaxRetries = &v
	}
	if run.Spec.StackRef == "" && opt.StackFile == "" {
		stack, appName, err := r.lookupStack(ctx, run)
		if err != nil {
			return opt, err
		}
		if stack != nil {
			run.Spec.StackRef = stack.Name
			if opt.StackFile == "" {
				if stack.Spec.StackFile != "" {
					opt.StackFile = stack.Spec.StackFile
				} else {
					opt.StackFile = fmt.Sprintf("stacks/%s.yaml", stack.Spec.Name)
				}
			}
			if opt.GitURL == "" {
				opt.GitURL = stack.Spec.GitURL
			}
			if opt.ImageRegistry == "" && stack.Spec.Defaults != nil {
				opt.ImageRegistry = stack.Spec.Defaults.ImageRegistry
			}
			if appName != "" {
				opt.ChangedApp = appName
			}
		}
	}
	if run.Spec.StackRef != "" {
		var stack tektondagv1alpha1.Stack
		if err := r.Get(ctx, types.NamespacedName{Name: run.Spec.StackRef, Namespace: run.Namespace}, &stack); err != nil {
			return opt, fmt.Errorf("stackRef %q: %w", run.Spec.StackRef, err)
		}
		if opt.StackFile == "" {
			if stack.Spec.StackFile != "" {
				opt.StackFile = stack.Spec.StackFile
			} else {
				opt.StackFile = fmt.Sprintf("stacks/%s.yaml", stack.Spec.Name)
			}
		}
		if opt.GitURL == "" {
			opt.GitURL = stack.Spec.GitURL
		}
		if opt.ImageRegistry == "" && stack.Spec.Defaults != nil {
			opt.ImageRegistry = stack.Spec.Defaults.ImageRegistry
		}
	}
	if opt.StackFile == "" {
		return opt, fmt.Errorf("stackFile or stackRef required")
	}
	switch run.Spec.Mode {
	case tektondagv1alpha1.StackRunModePR:
		if opt.ChangedApp == "" || opt.PRNumber == 0 {
			return opt, fmt.Errorf("changedApp and prNumber required for mode=pr")
		}
	case tektondagv1alpha1.StackRunModeMerge:
		if opt.ChangedApp == "" {
			return opt, fmt.Errorf("changedApp required for mode=merge")
		}
	case tektondagv1alpha1.StackRunModePromote:
		if opt.ReleaseVersion == "" || opt.TargetEnvironment == "" || opt.ChangedApp == "" {
			return opt, fmt.Errorf("releaseVersion, targetEnvironment, and changedApp required for mode=promote")
		}
	case tektondagv1alpha1.StackRunModeBootstrap:
		// ok
	default:
		return opt, fmt.Errorf("unknown mode %q", run.Spec.Mode)
	}
	return opt, nil
}

func repoShort(repo string) string {
	for i := len(repo) - 1; i >= 0; i-- {
		if repo[i] == '/' {
			return repo[i+1:]
		}
	}
	return repo
}

func (r *StackRunReconciler) lookupStack(ctx context.Context, run *tektondagv1alpha1.StackRun) (*tektondagv1alpha1.Stack, string, error) {
	var list tektondagv1alpha1.StackList
	if err := r.List(ctx, &list, client.InNamespace(run.Namespace)); err != nil {
		return nil, "", err
	}
	needle := run.Spec.ChangedApp
	for i := range list.Items {
		st := &list.Items[i]
		if run.Spec.StackFile != "" && (st.Spec.StackFile == run.Spec.StackFile || st.Name == run.Spec.StackFile) {
			return st, needle, nil
		}
		for _, app := range st.Spec.Apps {
			if needle != "" && (app.Name == needle || repoShort(app.Repo) == needle) {
				return st, app.Name, nil
			}
		}
	}
	if needle != "" || run.Spec.Mode == tektondagv1alpha1.StackRunModeBootstrap {
		if len(list.Items) == 1 && run.Spec.Mode == tektondagv1alpha1.StackRunModeBootstrap {
			return &list.Items[0], "", nil
		}
	}
	return nil, "", nil
}

func buildFromMode(mode tektondagv1alpha1.StackRunMode, opt pipeline.Options) (*unstructured.Unstructured, error) {
	switch mode {
	case tektondagv1alpha1.StackRunModePR:
		return pipeline.BuildPR(opt)
	case tektondagv1alpha1.StackRunModeBootstrap:
		return pipeline.BuildBootstrap(opt)
	case tektondagv1alpha1.StackRunModeMerge:
		return pipeline.BuildMerge(opt)
	case tektondagv1alpha1.StackRunModePromote:
		return pipeline.BuildPromote(opt)
	default:
		return nil, fmt.Errorf("unsupported mode %q", mode)
	}
}

// SetupWithManager sets up the controller with the Manager.
func (r *StackRunReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&tektondagv1alpha1.StackRun{}).
		Named("stackrun").
		Complete(r)
}
