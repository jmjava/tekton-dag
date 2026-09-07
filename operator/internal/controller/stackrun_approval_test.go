package controller

import (
	"testing"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func TestWaitingForApproval(t *testing.T) {
	run := &tektondagv1alpha1.StackRun{
		ObjectMeta: metav1.ObjectMeta{Name: "sr"},
		Spec: tektondagv1alpha1.StackRunSpec{
			Mode:            tektondagv1alpha1.StackRunModePromote,
			RequireApproval: true,
		},
	}
	if !waitingForApproval(run) {
		t.Fatal("expected waiting when requireApproval and approvedBy empty")
	}
	run.Spec.ApprovedBy = "alice"
	if waitingForApproval(run) {
		t.Fatal("should not wait after approvedBy is set")
	}
	run.Spec.ApprovedBy = ""
	run.Spec.RequireApproval = false
	if waitingForApproval(run) {
		t.Fatal("should not wait when requireApproval is false")
	}
	run.Spec.RequireApproval = true
	run.Spec.Mode = tektondagv1alpha1.StackRunModePR
	if waitingForApproval(run) {
		t.Fatal("approval wait is promote-only")
	}
}
