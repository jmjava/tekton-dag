package controller

import (
	"testing"

	tektondagv1alpha1 "github.com/jmjava/tekton-dag/operator/api/v1alpha1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func TestValidateStackHappyPath(t *testing.T) {
	stack := &tektondagv1alpha1.Stack{
		ObjectMeta: metav1.ObjectMeta{Name: "s"},
		Spec: tektondagv1alpha1.StackSpec{
			Name: "stack-one",
			Apps: []tektondagv1alpha1.StackApp{
				{Name: "fe", Repo: "o/fe", Role: "frontend", Downstream: []string{"bff"}},
				{Name: "bff", Repo: "o/bff", Role: "middleware"},
			},
		},
	}
	ok, topo, msg := validateStack(stack)
	if !ok {
		t.Fatalf("expected valid: %s", msg)
	}
	if len(topo) != 2 || topo[0] != "fe" {
		t.Fatalf("unexpected topo: %v", topo)
	}
}

func TestValidateStackMissingName(t *testing.T) {
	stack := &tektondagv1alpha1.Stack{
		Spec: tektondagv1alpha1.StackSpec{
			Apps: []tektondagv1alpha1.StackApp{{Name: "a", Repo: "r", Role: "frontend"}},
		},
	}
	ok, _, msg := validateStack(stack)
	if ok || msg == "" {
		t.Fatalf("expected invalid, got ok=%v msg=%q", ok, msg)
	}
}

func TestValidateStackUnknownDownstream(t *testing.T) {
	stack := &tektondagv1alpha1.Stack{
		Spec: tektondagv1alpha1.StackSpec{
			Name: "s",
			Apps: []tektondagv1alpha1.StackApp{
				{Name: "a", Repo: "r", Role: "frontend", Downstream: []string{"missing"}},
			},
		},
	}
	ok, _, _ := validateStack(stack)
	if ok {
		t.Fatal("expected invalid for unknown downstream")
	}
}
