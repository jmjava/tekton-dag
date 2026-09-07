The orchestrator is a central component of the Tekton DAG system, designed to manage and execute CI/CD pipelines effectively.

It serves as an in-cluster service that receives GitHub webhooks, dynamically resolving the appropriate stack for each repository. This orchestration enables seamless integration with various pipelines, including bootstrap, pull request, merge, and promote workflows.

When a webhook is triggered, the orchestrator processes the request and creates a StackRun. The operator then turns that StackRun into a Tekton PipelineRun. This includes handling the stack's secrets and configuration, ensuring that each application receives the necessary environment variables and resource profiles for successful deployment.

One of the key features of the orchestrator is its ability to perform health checks and readiness probes, which confirm that all applications are operational before any tests are executed. This minimizes the risk of failures during the testing phase.

The orchestrator also supports advanced features such as webhook HMAC verification for security. If a required secret is missing, the system fails closed, preventing unauthorized access.

With the recent updates, the orchestrator always creates StackRun custom resources instead of writing PipelineRuns itself. The operator then reconciles each StackRun into a Tekton PipelineRun. This allows for more structured management of the pipeline executions and better integration with the Kubernetes ecosystem.

Additionally, the orchestrator facilitates the promotion of images across different environments. Using the stack-promote pipeline, it can push images to various registries, ensuring that applications are consistently deployed across development, staging, and production environments.

As the system matures, the operator is the default runtime path. Flask always creates StackRuns, and the Helm chart installs the operator unless you turn it off.

The orchestrator's design and functionality are pivotal for achieving reliable and efficient CI/CD processes, making it an essential part of the Tekton DAG ecosystem.
