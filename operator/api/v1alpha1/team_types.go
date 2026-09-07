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

package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

	// TeamSpec is in-cluster team identity mirrored from teams/*/team.yaml.
	// Flask and the GUI overlay these CRs onto Git YAML when the cluster is reachable.
type TeamSpec struct {
	// Name is the logical team name.
	// +kubebuilder:validation:MinLength=1
	Name string `json:"name"`

	// TargetNamespace is where pipelines and apps for this team run.
	TargetNamespace string `json:"targetNamespace,omitempty"`

	// Cluster is a kube context or cluster name for the GUI.
	Cluster string `json:"cluster,omitempty"`

	ImageRegistry    string `json:"imageRegistry,omitempty"`
	CacheRepo        string `json:"cacheRepo,omitempty"`
	InterceptBackend string `json:"interceptBackend,omitempty"`

	MaxConcurrentRuns *int32 `json:"maxConcurrentRuns,omitempty"`
	MaxParallelBuilds *int32 `json:"maxParallelBuilds,omitempty"`

	// Stacks is an allowlist of stack file paths (e.g. stacks/stack-one.yaml).
	Stacks []string `json:"stacks,omitempty"`
}

// TeamStatus is observed team state.
type TeamStatus struct {
	ObservedGeneration int64              `json:"observedGeneration,omitempty"`
	Ready              bool               `json:"ready,omitempty"`
	Conditions         []metav1.Condition `json:"conditions,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Namespace",type=string,JSONPath=`.spec.targetNamespace`
// +kubebuilder:printcolumn:name="Ready",type=boolean,JSONPath=`.status.ready`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`

// Team is the Schema for the teams API.
type Team struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   TeamSpec   `json:"spec,omitempty"`
	Status TeamStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// TeamList contains a list of Team.
type TeamList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []Team `json:"items"`
}

func init() {
	SchemeBuilder.Register(&Team{}, &TeamList{})
}
