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

// StackRunMode is the pipeline mode for a StackRun.
// +kubebuilder:validation:Enum=pr;bootstrap;merge;promote;platform-upgrade
type StackRunMode string

const (
	StackRunModePR              StackRunMode = "pr"
	StackRunModeBootstrap       StackRunMode = "bootstrap"
	StackRunModeMerge           StackRunMode = "merge"
	StackRunModePromote         StackRunMode = "promote"
	StackRunModePlatformUpgrade StackRunMode = "platform-upgrade"
)

// StackRunSpec defines one desired pipeline execution.
type StackRunSpec struct {
	// Mode selects which Tekton pipeline to create.
	// +kubebuilder:validation:Required
	Mode StackRunMode `json:"mode"`

	// StackRef is the name of a Stack CR in the same namespace.
	// When empty, StackFile is used as a Tekton param (ConfigMap-era path).
	StackRef string `json:"stackRef,omitempty"`

	// StackFile is the stack YAML path param (e.g. stacks/stack-one.yaml).
	StackFile string `json:"stackFile,omitempty"`

	// GitURL / GitRevision for platform clone.
	GitURL      string `json:"gitUrl,omitempty"`
	GitRevision string `json:"gitRevision,omitempty"`

	// ImageRegistry and CacheRepo for builds.
	ImageRegistry string `json:"imageRegistry,omitempty"`
	CacheRepo     string `json:"cacheRepo,omitempty"`

	// ChangedApp is required for pr/merge/promote.
	ChangedApp string `json:"changedApp,omitempty"`

	// PRNumber is required for mode=pr.
	PRNumber int32 `json:"prNumber,omitempty"`

	// AppRevisions is a JSON object string of app→sha (PR mode).
	AppRevisions string `json:"appRevisions,omitempty"`

	// InterceptBackend for PR runs (telepresence|mirrord).
	InterceptBackend string `json:"interceptBackend,omitempty"`

	// DashboardURL and PRRepoURL optional PR comment links.
	DashboardURL string `json:"dashboardUrl,omitempty"`
	PRRepoURL    string `json:"prRepoUrl,omitempty"`

	// Promote fields.
	ReleaseVersion    string `json:"releaseVersion,omitempty"`
	TargetEnvironment string `json:"targetEnvironment,omitempty"`
	TargetRegistry    string `json:"targetRegistry,omitempty"`
	CredentialsSecret string `json:"credentialsSecret,omitempty"`
	RequireApproval   bool   `json:"requireApproval,omitempty"`
	ApprovedBy        string `json:"approvedBy,omitempty"`

	// Platform-upgrade fields (mode=platform-upgrade).
	// ActiveSlot / TargetSlot are blue|green style labels for dual-slot cutover.
	ActiveSlot string `json:"activeSlot,omitempty"`
	TargetSlot string `json:"targetSlot,omitempty"`
	// GateTaskRefs is an ordered list of Tekton Task names to run as registry
	// gates (e.g. suite-ready, volcano-drain). Core never embeds tool logic —
	// consumers install Tasks and pass names here.
	GateTaskRefs []string `json:"gateTaskRefs,omitempty"`
	// GateRegistry is an optional ConfigMap name holding the per-release gate list.
	// When set, the platform-upgrade pipeline may load gates from it; GateTaskRefs
	// still wins when non-empty.
	GateRegistry string `json:"gateRegistry,omitempty"`

	// Reliability (M13).
	Timeout    string `json:"timeout,omitempty"`
	MaxRetries *int32 `json:"maxRetries,omitempty"`

	// ServiceAccountName for TaskRuns (default tekton-pr-sa).
	ServiceAccountName string `json:"serviceAccountName,omitempty"`

	// PipelineNamespace overrides where PipelineRuns are created (default: StackRun namespace).
	PipelineNamespace string `json:"pipelineNamespace,omitempty"`
}

// StackRunStatus defines the observed state of StackRun.
type StackRunStatus struct {
	// ObservedGeneration is the last reconciled metadata.generation.
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`

	// PipelineRunName is the owned Tekton PipelineRun (orphan on delete).
	PipelineRunName string `json:"pipelineRunName,omitempty"`

	// Phase mirrors Tekton condition reason when known.
	Phase string `json:"phase,omitempty"`

	// Conditions represent the latest available observations.
	Conditions []metav1.Condition `json:"conditions,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Mode",type=string,JSONPath=`.spec.mode`
// +kubebuilder:printcolumn:name="PipelineRun",type=string,JSONPath=`.status.pipelineRunName`
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=`.status.phase`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`

// StackRun is the Schema for the stackruns API.
type StackRun struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   StackRunSpec   `json:"spec,omitempty"`
	Status StackRunStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// StackRunList contains a list of StackRun.
type StackRunList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []StackRun `json:"items"`
}

func init() {
	SchemeBuilder.Register(&StackRun{}, &StackRunList{})
}
