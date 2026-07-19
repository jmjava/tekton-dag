Tekton-DAG is a stack-aware CI/CD system built on Tekton, designed to model applications as directed acyclic graphs. This architecture allows for clear dependency management and efficient propagation of roles across different stages.

The system features four main pipelines: bootstrap, PR, merge or release, and promote. The bootstrap pipeline deploys the full stack initially, setting up the environment for further development. The PR pipeline focuses on intercepting changes, validating builds, and running tests. The merge or release pipeline promotes a release candidate to production, while the promote pipeline manages the transfer of images to different registries.

At the core of this architecture is the Flask orchestrator, which acts as the brain of the system. It listens for GitHub webhooks and processes requests through a REST API. When the STACKRUN_VIA_CRD option is enabled, runs are converted into StackRun custom resources, which are managed by a Kubernetes operator. This operator reconciles these custom resources into Tekton PipelineRuns, ensuring that the history of executions is preserved even if the original resources are deleted.

The architecture supports polyglot stacks, meaning it can handle applications built with various programming languages and frameworks. This flexibility is enhanced by the ability to integrate hook tasks, which can be customized for specific needs. 

The management GUI provides a user-friendly interface for teams to manage their pipelines, view runs, and monitor application statuses. The Helm chart facilitates multi-team deployments, allowing for isolation and efficient management of resources across different teams. 

Additionally, Tekton Results and Neo4j integration provide valuable insights into pipeline performance and historical data, enabling teams to make informed decisions based on past executions.

With the foundations of production hardening already shipped in Milestone 13, the system is evolving to enhance reliability and performance in real-world environments. Open items still include fine-tuning the handling of secrets and configuration, as well as improving observability and cross-cluster deployments.

The Kubernetes operator is a key component of this architecture. It allows for more granular control over stack management through Stack and StackRun custom resources. The operator is not yet the default runtime path, as the Helm configuration defaults to false for operator.enabled.

In summary, Tekton-DAG represents a robust and flexible architecture for modern CI/CD practices, focusing on efficiency, reliability, and user experience.
