Let's get tekton-dag running from scratch. The entire setup takes about five minutes on a local machine.

First, we create a Kind cluster with an integrated container registry. The kind-with-registry script provisions a single-node Kubernetes cluster and configures a local registry on port 5001 so we can push images without needing Docker Hub credentials.

Next, we install Tekton Pipelines into the cluster. The install-tekton script applies the official Tekton release manifests and waits for all controller pods to become ready.

Now we publish the build images — these are the containers that compile and test your code inside the pipeline. There are six: one each for npm, Maven, Gradle, pip, Composer, and mirrord. Each is built locally and pushed to the Kind registry. If you need multiple language versions — say Java 17 alongside Java 21 — the build-and-push script supports a matrix flag to generate all variants.

Finally, we apply the shared Tekton Tasks and Pipeline definitions with a single kubectl apply. These are the reusable building blocks: git-clone, resolve-stack, compile tasks for each build tool, Kaniko containerization, deployment, intercept setup for both Telepresence and mirrord, header propagation validation, and test execution.

That is the core platform. For optional components — Tekton Results with Postgres for pipeline history, Neo4j for the test-trace graph, or the Tekton Dashboard — there are dedicated install scripts in the scripts directory.

Four commands and we have a fully functional stack-aware CI/CD platform running locally. Let's see it in action.
