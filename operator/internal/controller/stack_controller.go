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

	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
)

// StackReconciler validates Stack CRs (no PipelineRuns).
type StackReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=tektondag.io,resources=stacks,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=tektondag.io,resources=stacks/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=tektondag.io,resources=stacks/finalizers,verbs=update
// +kubebuilder:rbac:groups="",resources=secrets;configmaps,verbs=get;list

func (r *StackReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	var stack tektondagv1alpha1.Stack
	if err := r.Get(ctx, req.NamespacedName, &stack); err != nil {
		if apierrors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, err
	}

	valid, topo, msg := validateStack(&stack)
	stack.Status.ObservedGeneration = stack.Generation
	stack.Status.Valid = valid
	stack.Status.TopoOrder = topo
	injectNS := stack.Namespace
	if stack.Spec.Defaults != nil && stack.Spec.Defaults.Namespace != "" {
		injectNS = stack.Spec.Defaults.Namespace
	}
	stack.Status.InjectionNamespace = injectNS
	missingS, missingC := r.injectionGaps(ctx, injectNS, &stack)
	stack.Status.MissingSecrets = missingS
	stack.Status.MissingConfigMaps = missingC

	cond := metav1.Condition{
		Type:               "Ready",
		Status:             metav1.ConditionTrue,
		Reason:             "Valid",
		Message:            "Stack passed structural validation",
		ObservedGeneration: stack.Generation,
	}
	if !valid {
		cond.Status = metav1.ConditionFalse
		cond.Reason = "Invalid"
		cond.Message = msg
	}
	meta.SetStatusCondition(&stack.Status.Conditions, cond)

	if err := r.Status().Update(ctx, &stack); err != nil {
		logger.Error(err, "unable to update Stack status")
		return ctrl.Result{}, err
	}
	return ctrl.Result{}, nil
}

func validateStack(stack *tektondagv1alpha1.Stack) (bool, []string, string) {
	if stack.Spec.Name == "" {
		return false, nil, "spec.name is required"
	}
	if len(stack.Spec.Apps) == 0 {
		return false, nil, "spec.apps must contain at least one app"
	}
	names := map[string]struct{}{}
	downstream := map[string][]string{}
	order := make([]string, 0, len(stack.Spec.Apps))
	for _, app := range stack.Spec.Apps {
		if app.Name == "" || app.Repo == "" || app.Role == "" {
			return false, nil, fmt.Sprintf("app %q requires name, repo, and role", app.Name)
		}
		if _, dup := names[app.Name]; dup {
			return false, nil, fmt.Sprintf("duplicate app name %q", app.Name)
		}
		names[app.Name] = struct{}{}
		downstream[app.Name] = app.Downstream
		order = append(order, app.Name)
	}
	for name, deps := range downstream {
		for _, d := range deps {
			if _, ok := names[d]; !ok {
				return false, nil, fmt.Sprintf("app %q references unknown downstream %q", name, d)
			}
		}
	}
	topo, err := topoSort(order, downstream)
	if err != nil {
		return false, nil, err.Error()
	}
	return true, topo, ""
}

func (r *StackReconciler) injectionGaps(ctx context.Context, ns string, stack *tektondagv1alpha1.Stack) ([]string, []string) {
	wantS, wantC := referencedInjection(stack)
	if len(wantS) == 0 && len(wantC) == 0 {
		return nil, nil
	}
	haveS := map[string]struct{}{}
	haveC := map[string]struct{}{}
	var sl corev1.SecretList
	if err := r.List(ctx, &sl, client.InNamespace(ns)); err == nil {
		for i := range sl.Items {
			haveS[sl.Items[i].Name] = struct{}{}
		}
	}
	var cl corev1.ConfigMapList
	if err := r.List(ctx, &cl, client.InNamespace(ns)); err == nil {
		for i := range cl.Items {
			haveC[cl.Items[i].Name] = struct{}{}
		}
	}
	var missS, missC []string
	for _, n := range wantS {
		if _, ok := haveS[n]; !ok {
			missS = append(missS, n)
		}
	}
	for _, n := range wantC {
		if _, ok := haveC[n]; !ok {
			missC = append(missC, n)
		}
	}
	return missS, missC
}

func referencedInjection(stack *tektondagv1alpha1.Stack) ([]string, []string) {
	var secrets, cms []string
	seenS, seenC := map[string]struct{}{}, map[string]struct{}{}
	for _, app := range stack.Spec.Apps {
		if app.Secrets != nil {
			for _, n := range app.Secrets.EnvFrom {
				if n == "" {
					continue
				}
				if _, ok := seenS[n]; !ok {
					seenS[n] = struct{}{}
					secrets = append(secrets, n)
				}
			}
			for _, m := range app.Secrets.VolumeMounts {
				if m.Secret == "" {
					continue
				}
				if _, ok := seenS[m.Secret]; !ok {
					seenS[m.Secret] = struct{}{}
					secrets = append(secrets, m.Secret)
				}
			}
		}
		if app.Config != nil {
			for _, n := range app.Config.EnvFrom {
				if n == "" {
					continue
				}
				if _, ok := seenC[n]; !ok {
					seenC[n] = struct{}{}
					cms = append(cms, n)
				}
			}
			for _, m := range app.Config.VolumeMounts {
				if m.ConfigMap == "" {
					continue
				}
				if _, ok := seenC[m.ConfigMap]; !ok {
					seenC[m.ConfigMap] = struct{}{}
					cms = append(cms, m.ConfigMap)
				}
			}
		}
	}
	return secrets, cms
}

func topoSort(apps []string, downstream map[string][]string) ([]string, error) {
	// Entry apps are never listed as someone else's downstream; walk forward.
	listed := map[string]struct{}{}
	for _, deps := range downstream {
		for _, d := range deps {
			listed[d] = struct{}{}
		}
	}
	var entries []string
	for _, a := range apps {
		if _, ok := listed[a]; !ok {
			entries = append(entries, a)
		}
	}
	if len(entries) == 0 && len(apps) > 0 {
		entries = []string{apps[0]}
	}
	seen := map[string]struct{}{}
	var result []string
	var walk func(string)
	walk = func(n string) {
		if _, ok := seen[n]; ok {
			return
		}
		seen[n] = struct{}{}
		result = append(result, n)
		for _, d := range downstream[n] {
			walk(d)
		}
	}
	for _, e := range entries {
		walk(e)
	}
	for _, a := range apps {
		walk(a)
	}
	if len(result) != len(apps) {
		return nil, fmt.Errorf("cycle detected in app downstream graph")
	}
	return result, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *StackReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&tektondagv1alpha1.Stack{}).
		Named("stack").
		Complete(r)
}
