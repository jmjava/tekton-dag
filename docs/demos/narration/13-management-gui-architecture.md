# Narration — Segment 13: Management GUI architecture (M12.2)

**Target duration:** ~2–4 minutes. **Visual:** browser dev server + Network tab.

## Script (edit for voice)

1. The Management GUI is a Vue three single-page app; the browser never holds cluster credentials.
2. Every Tekton or Kubernetes action goes to Flask behind REST paths under slash api, using the configured kubeconfig or in-cluster config.
3. The team switcher sets the active team; API paths follow the pattern slash api slash teams slash team name slash pipeline runs.
4. Trigger starts flows; Monitor polls runs; the DAG view shows stack relationships from server-resolved YAML.
5. For deployment, the Helm chart wires the backend to the right namespace and orchestrator endpoints.
