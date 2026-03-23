The Management GUI is a Vue three single-page app; the browser never holds cluster credentials.

Every Tekton or Kubernetes action goes to Flask behind REST paths under slash api, using the configured kubeconfig or in-cluster config.

The team switcher sets the active team; API paths follow the pattern slash api slash teams slash team name slash pipeline runs.

Trigger starts flows; Monitor polls runs; the DAG view shows stack relationships from server-resolved YAML.

For deployment, the Helm chart wires the backend to the right namespace and orchestrator endpoints.
