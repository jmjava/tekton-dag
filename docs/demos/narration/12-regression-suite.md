# Narration — Segment 12: Full regression suite (M12.2)

**Target duration:** ~3–5 minutes. **Visual:** terminal + optional `kubectl get pipelinerun`.

## Script (edit for voice)

1. We verify tekton-dag in layers — unit tests alone are not enough for a cluster release.
2. Without Kubernetes, Phase one still validates stack YAML and registry wiring, and pytest exercises the Python services.
3. With a cluster, we run a scripted driver: port prep, a real `stack-dag-verify` pipeline to succeeded, Newman against the orchestrator, and optionally Tekton Results.
4. Here is `run-regression-agent.sh` — watch for Phase two passed and regression exit code zero.
5. That line means our scripted bar is clear for documentation updates or merge.

*(Replace dashes with script names when recording: `run-regression-agent.sh`.)*
