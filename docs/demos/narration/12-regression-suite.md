# Narration — Segment 12: Full regression suite (M12.2)

**Target duration:** ~3–5 minutes. **Visual:** terminal + optional `kubectl get pipelinerun`.

## Script (edit for voice)

1. We verify tekton-dag in layers — unit tests alone are not enough for a cluster release.
2. Without Kubernetes, phase one still validates stack YAML and registry wiring, and pytest exercises the Python services.
3. With a cluster, we run a scripted driver: port prep, a real stack-dag-verify PipelineRun until it reaches Succeeded, Newman against the orchestrator, and optionally Tekton Results.
4. Here is the run regression agent shell script — watch for phase two passed and regression exit code zero.
5. That line means our scripted quality bar is clear for documentation updates or merge.
