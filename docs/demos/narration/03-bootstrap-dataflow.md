Now let's bootstrap a stack and watch data flow through it.

When we trigger the bootstrap pipeline, every service in the stack gets built and deployed. The pipeline begins by cloning the platform repo and running resolve-stack — this task reads the stack YAML, parses the DAG, and outputs the list of apps, their build tools, and the propagation chain. Then it clones each application repository using SSH credentials.

Next, the build-select-tool-apps task determines which compile task to invoke for each app — npm for the Vue front-end, Maven for the Spring Boot BFF and API. The compile tasks run inside parameterized build images, then Kaniko packages each app into a container and pushes it to the registry. Finally, the deploy-full-stack task deploys all services into the cluster.

Once all services are running, let's trace a request through the stack. A user hits the Vue front-end. The front-end makes an API call to the BFF. In the stack definition, the front-end's propagation role is originator — it sets the x-dev-session header on all outgoing requests.

The BFF receives the request. Its role is forwarder — it reads the incoming header, stores it in request context, and attaches it to every downstream call. The API is the terminal — it accepts the header for routing and logging but does not forward further.

In normal operation, this header is absent and traffic flows to the standard deployments. But when a PR pipeline runs, the header becomes the routing key that directs test traffic to the PR-specific build. That is the foundation of traffic interception, and it is what we will see next.
