How do we know the platform itself works? Unit tests cover the Python services. But a CI/CD platform that manages Kubernetes clusters, Tekton pipelines, and container registries needs more than pytest to prove it is ready.

tekton-dag verifies itself in layers — we call them phases.

Phase one runs without a Kubernetes cluster. It validates the stack YAML files against the schema, checks that the registry mapping resolves every app to the correct repository, and runs pytest across the orchestrator, the shared tekton-dag-common library, and the management GUI backend. These are fast — usually under a minute — and they catch regressions in the Python codebase, manifest generation, and stack resolution logic.

Phase two requires a live cluster. The regression driver script starts by preparing ports — killing any stale port-forwards from previous runs so nothing collides. Then it submits a real stack-dag-verify PipelineRun to the cluster. This pipeline clones the platform repo, resolves the stack graph, and validates that every task definition and pipeline parameter is consistent. The script watches the PipelineRun until it reaches Succeeded or fails.

If the PipelineRun passes, the script port-forwards to the orchestrator and runs Newman against it — the full Postman collection that exercises health checks, stack listing, manual run triggers, webhook parsing, and graph endpoints. This proves the orchestrator is functional on a real cluster, not just passing mocked unit tests.

Optionally, phase two also verifies Tekton Results. The script checks that completed PipelineRuns appear in the Postgres-backed Results API, confirming the persistence layer is operational.

The regression agent script ties it all together. It runs phase one, and if everything passes, proceeds to phase two. The script exits with code zero only when all phases complete successfully. Any failure — a pytest assertion, a PipelineRun timeout, a Newman test error — produces a non-zero exit code with the failing phase clearly identified in the output.

For automated workflows, the agent iterates: fix the failure, re-run the script, repeat until exit code zero. The output is structured so that both humans and CI systems can parse which phase failed and why.

Watch the terminal. Phase one — pytest passes, stack validation passes. Phase two — port prep, PipelineRun submitted, waiting for Succeeded, Newman collection running, all assertions pass. Regression exit code zero.

Layered verification. No cluster available? Phase one still catches Python regressions and manifest errors. Full cluster? Phase two proves the platform end to end. That is the regression suite.
