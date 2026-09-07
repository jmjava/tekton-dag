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

	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
)

// TeamReconciler records Ready status for Team CRs (no PipelineRuns).
type TeamReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=tektondag.io,resources=teams,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=tektondag.io,resources=teams/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=tektondag.io,resources=teams/finalizers,verbs=update

func (r *TeamReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)
	var team tektondagv1alpha1.Team
	if err := r.Get(ctx, req.NamespacedName, &team); err != nil {
		if apierrors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, err
	}
	ready := team.Spec.Name != ""
	team.Status.ObservedGeneration = team.Generation
	team.Status.Ready = ready
	cond := metav1.Condition{
		Type:               "Ready",
		Status:             metav1.ConditionTrue,
		Reason:             "Valid",
		Message:            "Team spec accepted",
		ObservedGeneration: team.Generation,
	}
	if !ready {
		cond.Status = metav1.ConditionFalse
		cond.Reason = "Invalid"
		cond.Message = "spec.name is required"
	}
	meta.SetStatusCondition(&team.Status.Conditions, cond)
	if err := r.Status().Update(ctx, &team); err != nil {
		logger.Error(err, "unable to update Team status")
		return ctrl.Result{}, err
	}
	return ctrl.Result{}, nil
}

func (r *TeamReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&tektondagv1alpha1.Team{}).
		Named("team").
		Complete(r)
}
