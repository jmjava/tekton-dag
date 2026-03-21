# Environments and clusters

This project’s docs and demos often talk about **two traffic paths** (PR vs non-PR) in a cluster. That is **not** the same as “this cluster is production.”

## How we name things

| Term | Meaning |
|------|--------|
| **Validation / pre-production cluster** | A **dedicated** Kubernetes cluster (or namespace slice) used to **build, deploy, and test** changes. It is usually **similar in shape** to production (same kinds of services, ingress, policies) so tests are realistic. **Pipelines and intercept demos run here.** |
| **Production cluster** | Where **released** workloads run for real users. Code and images are **promoted** here **after** validation — it is a **separate** cluster (or strictly separated environment), not the same place PR pipelines mutate. |
| **Baseline deployment** (or **mainline**) | The **non-PR** revision of a service **in the validation cluster** — the “steady” line already merged and deployed there. Demos that used to say “production” for this path mean **baseline**, not customer production. |
| **PR deployment** | An **ephemeral** revision deployed **alongside** the baseline **in the validation cluster**, reachable when requests carry the dev-session header. |

So: **“normal traffic”** in intercept diagrams = traffic to the **baseline** pods in the **validation** environment, **unless** the document explicitly says it is about the production cluster.

## Scripts and promotion

- `scripts/promote-pipelines.sh` moves Tekton YAML between namespaces (e.g. test → prod-facing namespace). That is an **operator-controlled promotion step**; it does not imply that PR validation runs in the production cluster.
- Regression and E2E scripts target **whatever cluster your kubeconfig points at** — treat that as validation unless you intentionally point at production (not recommended for destructive tests).

## Demos and narration

Demo videos and Manim scenes use **baseline / mainline** wording for the non-PR path so they stay accurate for teams that **only** run pipelines in a validation cluster and ship artifacts onward to production separately.
