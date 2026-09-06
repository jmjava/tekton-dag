# Multi-repo artifact map

Academic reviewers will not reconstruct this from milestone notes. Treat **tekton-dag** as the hub artifact and the other GitHub repos as **constituents** of one software ecosystem (the same language SESoS uses).

```text
                    ┌─────────────────────────────────────┐
                    │  Hub: github.com/jmjava/tekton-dag  │
                    │  pipelines, stacks, orchestrator,   │
                    │  Helm, operator, libs, docs, demos  │
                    └──────────────┬──────────────────────┘
           ┌───────────────┬───────┼────────┬──────────────┐
           ▼               ▼       ▼        ▼              ▼
     sample apps      baggage    docgen   Pages        (optional)
     (6 Git repos)    (in-tree   sibling  jmjava.      operator
                      libs/)     repo     github.io    in-tree
```

## Hub (this repository)

| Path | Role in a paper |
|------|-----------------|
| `stacks/*.yaml`, `stacks/schema.json` | Application DAG exemplar |
| `pipeline/`, `tasks/` | Universal pipeline family |
| `orchestrator/` | Webhook + REST control plane |
| `helm/tekton-dag/` | Multi-team packaging |
| `operator/` | Optional CRD path (`Stack`, `StackRun`) |
| `libs/baggage-*` | C2 libraries (Maven, npm, pip, Composer) |
| `libs/tekton-dag-common/` | Shared resolver / PipelineRun builder |
| `management-gui/` | Operator UI (not a research claim) |
| `scripts/run-regression*.sh` | Functional validation entrypoint |
| `docs/demos/` | Narration + Manim + composed MP4s |
| `docs/research/` | Academic packaging (this tree) |

Canonical clone: `https://github.com/jmjava/tekton-dag`  
Demo site: `https://jmjava.github.io/tekton-dag/`

## Constituent application repos (runtime graph)

Documented in [`sample-repos/README.md`](../../sample-repos/README.md). Pipelines clone these over SSH/HTTPS; they are **not** git submodules of the hub.

| Repository | Stack role (stack-one) | Toolchain |
|------------|------------------------|-----------|
| [jmjava/tekton-dag-vue-fe](https://github.com/jmjava/tekton-dag-vue-fe) | originator / frontend | npm, Vue |
| [jmjava/tekton-dag-spring-boot](https://github.com/jmjava/tekton-dag-spring-boot) | forwarder / BFF | Maven, Spring Boot |
| [jmjava/tekton-dag-spring-boot-gradle](https://github.com/jmjava/tekton-dag-spring-boot-gradle) | terminal / API | Maven/Gradle, Spring Boot |
| [jmjava/tekton-dag-flask](https://github.com/jmjava/tekton-dag-flask) | test stacks | pip, Flask |
| [jmjava/tekton-dag-php](https://github.com/jmjava/tekton-dag-php) | test stacks | Composer, PHP |
| [jmjava/tekton-dag-spring-legacy](https://github.com/jmjava/tekton-dag-spring-legacy) | test stacks | Maven, servlet |

Additional graphs: `stack-two-vendor.yaml`, `single-app.yaml`, `single-flask-app.yaml`, `test-stack-*.yaml`.

## Sibling / extracted tooling

| Repository or tree | Status | Paper treatment |
|--------------------|--------|-----------------|
| [jmjava/documentation-generator](https://github.com/jmjava/documentation-generator) (`docgen`) | Intended extract; in-tree copy under `documentation-generator/` | Supporting artifact for C5 (how demos are produced). **Do not** make it the main contribution of the ICSE demo paper. |
| `reference-architecture-poc` (historical parent) | See [`SHARING-BACK.md`](../../SHARING-BACK.md) | Cite only as provenance; tekton-dag is the standalone artifact. |

## What a reviewer should be able to do without SSH to all six apps

Minimum **read-only** path (no cluster):

1. Open the Pages demo (segments 01, 04, 05).
2. Read `stacks/stack-one.yaml` and `docs/DAG-AND-PROPAGATION.md`.
3. Run `scripts/run-regression.sh --local-only` (Phase 1 DAG + unit tests).

Minimum **functional** path (Kind): [`DO-THIS-LOCAL.md`](../../DO-THIS-LOCAL.md) and the README quick start. This currently **exceeds** the informal 30-minute artifact-eval install budget — see [gaps.md](gaps.md).

## Version pin for a submission

Before HotCRP:

1. Create a GitHub **release** (e.g. `v0.1.0-workshop`) of tekton-dag.
2. Archive that commit on [Zenodo](https://zenodo.org/) (GitHub–Zenodo webhook) → DOI.
3. Optionally push the same snapshot to [Software Heritage](https://www.softwareheritage.org/).
4. Put the DOI in the paper, `CITATION.cff`, and the demo abstract URL line.
5. Record the **commit SHAs** of the six sample repos used in the recorded demo (they move independently).

GitHub HEAD is not a stable academic identifier.
