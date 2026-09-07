package controller

import (
	"testing"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func TestValidateStackAdmissionRejectsEmptyApps(t *testing.T) {
	stack := &tektondagv1alpha1.Stack{
		ObjectMeta: metav1.ObjectMeta{Name: "s"},
		Spec:       tektondagv1alpha1.StackSpec{Name: "s"},
	}
	_, err := validateStackAdmission(stack)
	if err == nil {
		t.Fatal("expected admission error")
	}
}

func TestValidateStackAdmissionOK(t *testing.T) {
	stack := &tektondagv1alpha1.Stack{
		ObjectMeta: metav1.ObjectMeta{Name: "s"},
		Spec: tektondagv1alpha1.StackSpec{
			Name: "s",
			Apps: []tektondagv1alpha1.StackApp{{Name: "a", Repo: "r", Role: "frontend"}},
		},
	}
	_, err := validateStackAdmission(stack)
	if err != nil {
		t.Fatal(err)
	}
}

func TestRepoShort(t *testing.T) {
	if got := repoShort("jmjava/tekton-dag-vue-fe"); got != "tekton-dag-vue-fe" {
		t.Fatalf("got %s", got)
	}
	if got := repoShort("demo-fe"); got != "demo-fe" {
		t.Fatalf("got %s", got)
	}
}
