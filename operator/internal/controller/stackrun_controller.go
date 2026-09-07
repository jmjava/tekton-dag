/*
Copyright 2026.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific license governing permissions and
limitations under the License.
*/

package controller

import (
	"context"
	"fmt"
	"strconv"
	"time"

	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/util/retry"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/log"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
	"github.com/jmjava/tekton-dag/operator/internal/pipeline"
)

const (
	// Label marking PipelineRuns created for a StackRun. OwnerReference is not
	// set (orphan on StackRun delete) so Tekton Results history survives.
	labelStackRun = "tektondag.io/stackrun"

	pipelineStatusRetry = 15 * time.Second
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

	if run.Status.PipelineRunName != "" {
		return r.syncPipelineStatus(ctx, &run)
	}

	if waitingForApproval(&run) {
		return r.pendingApproval(ctx, &run)
	}

	prName, err := r.findExistingPipelineRun(ctx, &run)
	if err != nil {
		return ctrl.Result{}, err
	}
	if prName == "" {
		opt, err := r.optionsFromStackRun(ctx, &run)
		if err != nil {
			return r.fail(ctx, &run, "InvalidSpec", err.Error())
		}
		if opt.ContinueFrom != "" {
			if err := r.fillContinue(ctx, &run, &opt); err != nil {
				return r.fail(ctx, &run, "ContinueFailed", err.Error())
			}
		}
		pr, err := buildFromMode(run.Spec.Mode, opt)
		if err != nil {
			return r.fail(ctx, &run, "BuildFailed", err.Error())
		}
		pr.SetName(run.Name)
		pr.SetNamespace(pipelineNamespace(&run))
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
			if !apierrors.IsAlreadyExists(err) {
				logger.Error(err, "failed to create PipelineRun")
				return r.fail(ctx, &run, "CreateFailed", err.Error())
			}
		}
		prName = pr.GetName()
	}

	if err := r.patchStatus(ctx, &run, func(latest *tektondagv1alpha1.StackRun) {
		latest.Status.PipelineRunName = prName
		latest.Status.ObservedGeneration = latest.Generation
		latest.Status.Phase = "Pending"
		meta.SetStatusCondition(&latest.Status.Conditions, metav1.Condition{
			Type:               "Ready",
			Status:             metav1.ConditionFalse,
			Reason:             "PipelineRunCreated",
			Message:            fmt.Sprintf("Created PipelineRun %s", prName),
			ObservedGeneration: latest.Generation,
		})
	}); err != nil {
		return ctrl.Result{}, err
	}
	return ctrl.Result{RequeueAfter: pipelineStatusRetry}, nil
}

func waitingForApproval(run *tektondagv1alpha1.StackRun) bool {
	return run.Spec.Mode == tektondagv1alpha1.StackRunModePromote &&
		run.Spec.RequireApproval &&
		run.Spec.ApprovedBy == ""
}

func (r *StackRunReconciler) pendingApproval(ctx context.Context, run *tektondagv1alpha1.StackRun) (ctrl.Result, error) {
	err := r.patchStatus(ctx, run, func(latest *tektondagv1alpha1.StackRun) {
		latest.Status.ObservedGeneration = latest.Generation
		latest.Status.Phase = "PendingApproval"
		meta.SetStatusCondition(&latest.Status.Conditions, metav1.Condition{
			Type:               "Ready",
			Status:             metav1.ConditionFalse,
			Reason:             "PendingApproval",
			Message:            "requireApproval is set; patch spec.approvedBy to create the PipelineRun",
			ObservedGeneration: latest.Generation,
		})
	})
	return ctrl.Result{}, err
}

func (r *StackRunReconciler) syncPipelineStatus(ctx context.Context, run *tektondagv1alpha1.StackRun) (ctrl.Result, error) {
	prNS := pipelineNamespace(run)
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
	if err := r.patchStatus(ctx, run, func(latest *tektondagv1alpha1.StackRun) {
		latest.Status.Phase = phase
		latest.Status.ObservedGeneration = latest.Generation
		ready := metav1.ConditionFalse
		reason := phase
		msg := fmt.Sprintf("PipelineRun %s phase=%s", latest.Status.PipelineRunName, phase)
		if phase == "Succeeded" {
			ready = metav1.ConditionTrue
		}
		meta.SetStatusCondition(&latest.Status.Conditions, metav1.Condition{
			Type:               "Ready",
			Status:             ready,
			Reason:             reason,
			Message:            msg,
			ObservedGeneration: latest.Generation,
		})
	}); err != nil {
		return ctrl.Result{}, err
	}
	if phase == "Succeeded" || phase == "Failed" || phase == "Cancelled" {
		return ctrl.Result{}, nil
	}
	return ctrl.Result{RequeueAfter: pipelineStatusRetry}, nil
}

func (r *StackRunReconciler) fail(ctx context.Context, run *tektondagv1alpha1.StackRun, reason, msg string) (ctrl.Result, error) {
	err := r.patchStatus(ctx, run, func(latest *tektondagv1alpha1.StackRun) {
		latest.Status.ObservedGeneration = latest.Generation
		latest.Status.Phase = "Error"
		meta.SetStatusCondition(&latest.Status.Conditions, metav1.Condition{
			Type:               "Ready",
			Status:             metav1.ConditionFalse,
			Reason:             reason,
			Message:            msg,
			ObservedGeneration: latest.Generation,
		})
	})
	return ctrl.Result{}, err
}

func (r *StackRunReconciler) patchStatus(ctx context.Context, run *tektondagv1alpha1.StackRun, mutate func(*tektondagv1alpha1.StackRun)) error {
	key := types.NamespacedName{Name: run.Name, Namespace: run.Namespace}
	return retry.RetryOnConflict(retry.DefaultBackoff, func() error {
		var latest tektondagv1alpha1.StackRun
		if err := r.Get(ctx, key, &latest); err != nil {
			return err
		}
		mutate(&latest)
		if err := r.Status().Update(ctx, &latest); err != nil {
			return err
		}
		latest.DeepCopyInto(run)
		return nil
	})
}

func pipelineNamespace(run *tektondagv1alpha1.StackRun) string {
	if run.Spec.PipelineNamespace != "" {
		return run.Spec.PipelineNamespace
	}
	return run.Namespace
}

// findExistingPipelineRun returns a PipelineRun already created for this StackRun
// (deterministic name = StackRun name, or label tektondag.io/stackrun).
func (r *StackRunReconciler) findExistingPipelineRun(ctx context.Context, run *tektondagv1alpha1.StackRun) (string, error) {
	ns := pipelineNamespace(run)
	pr := &unstructured.Unstructured{}
	pr.SetGroupVersionKind(pipeline.PipelineRunGVK)
	if err := r.Get(ctx, types.NamespacedName{Name: run.Name, Namespace: ns}, pr); err == nil {
		return pr.GetName(), nil
	} else if !apierrors.IsNotFound(err) {
		return "", err
	}
	list := &unstructured.UnstructuredList{}
	list.SetGroupVersionKind(pipeline.PipelineRunGVK)
	list.SetKind("PipelineRunList")
	if err := r.List(ctx, list, client.InNamespace(ns), client.MatchingLabels{labelStackRun: run.Name}); err != nil {
		return "", err
	}
	if len(list.Items) == 0 {
		return "", nil
	}
	return list.Items[0].GetName(), nil
}

func mapPipelineRunToStackRun(_ context.Context, obj client.Object) []ctrl.Request {
	labels := obj.GetLabels()
	if labels == nil {
		return nil
	}
	name := labels[labelStackRun]
	if name == "" {
		return nil
	}
	return []ctrl.Request{{NamespacedName: types.NamespacedName{Name: name, Namespace: obj.GetNamespace()}}}
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
		ContinueFrom:       run.Spec.ContinueFrom,
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

	var stack *tektondagv1alpha1.Stack
	if run.Spec.StackRef != "" {
		got := &tektondagv1alpha1.Stack{}
		if err := r.Get(ctx, types.NamespacedName{Name: run.Spec.StackRef, Namespace: run.Namespace}, got); err != nil {
			return opt, fmt.Errorf("stackRef %q: %w", run.Spec.StackRef, err)
		}
		stack = got
	} else if opt.StackFile == "" {
		found, appName, err := r.lookupStack(ctx, run)
		if err != nil {
			return opt, err
		}
		if found != nil {
			stack = found
			if appName != "" {
				opt.ChangedApp = appName
			}
		}
	}
	if stack != nil {
		applyStackDefaults(&opt, stack)
	}
	if opt.ContinueFrom != "" {
		return opt, nil
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

func applyStackDefaults(opt *pipeline.Options, stack *tektondagv1alpha1.Stack) {
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
	if opt.ContinueFrom != "" || opt.WorkspacePVC != "" {
		return pipeline.BuildPRContinue(opt)
	}
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
	pr := &unstructured.Unstructured{}
	pr.SetGroupVersionKind(pipeline.PipelineRunGVK)
	return ctrl.NewControllerManagedBy(mgr).
		For(&tektondagv1alpha1.StackRun{}).
		Watches(pr, handler.EnqueueRequestsFromMapFunc(mapPipelineRunToStackRun)).
		Named("stackrun").
		Complete(r)
}
