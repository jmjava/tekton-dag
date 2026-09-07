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

	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/webhook"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
)

// +kubebuilder:webhook:path=/validate-tektondag-io-v1alpha1-stack,mutating=false,failurePolicy=fail,sideEffects=None,groups=tektondag.io,resources=stacks,verbs=create;update,versions=v1alpha1,name=vstack.tektondag.io,admissionReviewVersions=v1

var _ webhook.CustomValidator = &StackReconciler{}

func (r *StackReconciler) SetupWebhookWithManager(mgr ctrl.Manager) error {
	return ctrl.NewWebhookManagedBy(mgr).
		For(&tektondagv1alpha1.Stack{}).
		WithValidator(r).
		Complete()
}

func (r *StackReconciler) ValidateCreate(_ context.Context, obj runtime.Object) (admission.Warnings, error) {
	return validateStackAdmission(obj)
}

func (r *StackReconciler) ValidateUpdate(_ context.Context, _, newObj runtime.Object) (admission.Warnings, error) {
	return validateStackAdmission(newObj)
}

func (r *StackReconciler) ValidateDelete(_ context.Context, _ runtime.Object) (admission.Warnings, error) {
	return nil, nil
}

func validateStackAdmission(obj runtime.Object) (admission.Warnings, error) {
	stack, ok := obj.(*tektondagv1alpha1.Stack)
	if !ok {
		return nil, fmt.Errorf("expected Stack, got %T", obj)
	}
	valid, _, msg := validateStack(stack)
	if !valid {
		return nil, fmt.Errorf("%s", msg)
	}
	return nil, nil
}
