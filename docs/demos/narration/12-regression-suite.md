We verify tekton-dag in layers — unit tests alone are not enough for a cluster release.

Without Kubernetes, phase one still validates stack YAML and registry wiring, and pytest exercises the Python services.

With a cluster, we run a scripted driver: port prep, a real stack-dag-verify PipelineRun until it reaches Succeeded, Newman against the orchestrator, and optionally Tekton Results.

Here is the run regression agent shell script — watch for phase two passed and regression exit code zero.

That line means our scripted quality bar is clear for documentation updates or merge.
