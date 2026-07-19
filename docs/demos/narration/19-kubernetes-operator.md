The Kubernetes operator for tekton-dag is designed to be the primary interface for managing stack-based pipelines. It utilizes custom resources to represent the desired state of applications and their execution flows.

At the core of this operator are two key custom resource definitions: Stack and StackRun. The Stack resource defines the application structure, while the StackRun resource is responsible for executing specific operations, such as pull requests, bootstraps, merges, and promotions.

The flow begins with a GitHub webhook or a direct API call to the Flask orchestrator. This orchestrator processes the request and, when configured to operate with the CRD path, creates a StackRun resource. The tekton-dag-operator then takes over, monitoring the StackRun and converting it into Tekton PipelineRuns.

This architecture enables better management of the pipeline lifecycle, ensuring that the results of each execution are retained even when StackRuns are deleted. By orphaning PipelineRuns upon deletion of their associated StackRuns, the operator preserves the history of results, which is crucial for tracking and auditing.

The operator is built using Go and Kubebuilder, providing a robust foundation for managing Kubernetes resources. The implementation includes features like validation of stacks and the orchestration of pipeline executions, all designed to enhance the developer experience and improve operational efficiency.

Foundations for the operator have been established, including integration with Helm and the Flask orchestrator. However, the operator is not yet the default runtime path. The configuration for enabling this operator includes setting the STACKRUN_VIA_CRD environment variable and the Helm operator.enabled flag, which defaults to false.

This new approach aims to streamline the pipeline management process, making it more GitOps-friendly by relying on desired-state custom resources rather than direct API calls.
