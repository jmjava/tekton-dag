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
	"k8s.io/apimachinery/pkg/runtime"
)

// StackSpec defines the desired state of Stack (mirrors stacks/schema.json).
type StackSpec struct {
	// Name is the logical stack name (e.g. stack-one).
	// +kubebuilder:validation:MinLength=1
	Name string `json:"name"`

	// Description is optional human-readable text.
	Description string `json:"description,omitempty"`

	// StackFile is the conventional path used by Tekton params (e.g. stacks/stack-one.yaml).
	StackFile string `json:"stackFile,omitempty"`

	// GitURL is the platform / stack definition repository.
	GitURL string `json:"gitUrl,omitempty"`

	// Team is an optional team label for multi-team installs.
	Team string `json:"team,omitempty"`

	// Propagation header / baggage settings.
	Propagation *StackPropagation `json:"propagation,omitempty"`

	// Defaults applied to apps when not overridden.
	Defaults *StackDefaults `json:"defaults,omitempty"`

	// Apps is the application DAG.
	// +kubebuilder:validation:MinItems=1
	Apps []StackApp `json:"apps"`
}

// StackPropagation mirrors stack YAML propagation block.
type StackPropagation struct {
	HeaderName string `json:"headerName,omitempty"`
	BaggageKey string `json:"baggageKey,omitempty"`
	Strategy   string `json:"strategy,omitempty"`
}

// StackDefaults mirrors stack YAML defaults block.
type StackDefaults struct {
	Namespace     string `json:"namespace,omitempty"`
	ImageRegistry string `json:"imageRegistry,omitempty"`
	ServicePort   string `json:"servicePort,omitempty"`
	ContainerPort string `json:"containerPort,omitempty"`
}

// StackApp is one node in the stack DAG.
type StackApp struct {
	Name             string                `json:"name"`
	Repo             string                `json:"repo"`
	Role             string                `json:"role"`
	PropagationRole  string                `json:"propagationRole,omitempty"`
	ContainerPort    string                `json:"containerPort,omitempty"`
	ContextDir       string                `json:"contextDir,omitempty"`
	Dockerfile       string                `json:"dockerfile,omitempty"`
	Build            *StackAppBuild        `json:"build,omitempty"`
	Downstream       []string              `json:"downstream,omitempty"`
	Tests            *runtime.RawExtension `json:"tests,omitempty"`
	Secrets          *StackInjection       `json:"secrets,omitempty"`
	Config           *StackInjection       `json:"config,omitempty"`
}

// StackAppBuild describes how to compile/containerize an app.
type StackAppBuild struct {
	Tool         string `json:"tool,omitempty"`
	Runtime      string `json:"runtime,omitempty"`
	JavaVersion  string `json:"javaVersion,omitempty"`
	NodeVersion  string `json:"nodeVersion,omitempty"`
	PythonVersion string `json:"pythonVersion,omitempty"`
	PhpVersion   string `json:"phpVersion,omitempty"`
	BuildCommand string `json:"buildCommand,omitempty"`
}

// StackInjection is secrets or config envFrom / volumeMounts.
type StackInjection struct {
	EnvFrom      []string                `json:"envFrom,omitempty"`
	VolumeMounts []StackVolumeMount      `json:"volumeMounts,omitempty"`
}

// StackVolumeMount mounts a Secret or ConfigMap as files.
type StackVolumeMount struct {
	Secret    string `json:"secret,omitempty"`
	ConfigMap string `json:"configMap,omitempty"`
	MountPath string `json:"mountPath"`
}

// StackStatus defines the observed state of Stack.
type StackStatus struct {
	// ObservedGeneration is the last reconciled metadata.generation.
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`

	// Valid is true when the stack passed structural validation.
	Valid bool `json:"valid,omitempty"`

	// TopoOrder is the resolved app order (entry first).
	TopoOrder []string `json:"topoOrder,omitempty"`

	// MissingSecrets referenced by apps but absent in the injection namespace.
	MissingSecrets []string `json:"missingSecrets,omitempty"`

	// MissingConfigMaps referenced by apps but absent in the injection namespace.
	MissingConfigMaps []string `json:"missingConfigMaps,omitempty"`

	// InjectionNamespace is where Secrets/ConfigMaps were checked.
	InjectionNamespace string `json:"injectionNamespace,omitempty"`

	// Conditions represent the latest available observations.
	Conditions []metav1.Condition `json:"conditions,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Valid",type=boolean,JSONPath=`.status.valid`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`

// Stack is the Schema for the stacks API.
type Stack struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   StackSpec   `json:"spec,omitempty"`
	Status StackStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// StackList contains a list of Stack.
type StackList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []Stack `json:"items"`
}

func init() {
	SchemeBuilder.Register(&Stack{}, &StackList{})
}
