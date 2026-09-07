# ACM / ICSE artifact checklist

Mapped to [ACM Artifact Review and Badging v1.1](https://www.acm.org/publications/policies/artifact-review-and-badging-current) and the [ICSE 2027 Artifact Evaluation CFP](https://conf.researchr.org/track/icse-2027/icse-2027-artifact-evaluation). Tool-demo papers may submit artifacts **after acceptance**.

## Badge targets

| Badge | Realistic for first submission? | Blocker |
|-------|----------------------------------|---------|
| **Artifacts Available** | After a Zenodo (or Software Heritage) DOI on a tagged release | GitHub URL is **not** archival. CFP: personal pages / plain GitHub generally do not qualify. |
| **Artifacts Evaluated — Functional** | Plausible if reviewers get a **pre-warmed Kind or k3d image** plus `--local-only` regression | Install from scratch (Kind + Tekton + images + intercepts) exceeds the ~30 min AE guideline. |
| **Artifacts Evaluated — Reusable** | Stretch | Needs textbook docs, version pins of sample repos, and a “replay paper figures” script. |
| **Results Reproduced / Replicated** | No | Requires a later independent paper. |

## Required files (AE CFP)

| Item | Status in this PR | Remaining |
|------|-------------------|-----------|
| `LICENSE` | Apache-2.0 added | Keep SPDX in new files where practical |
| `README` with Purpose / Setup / Usage | Root README is operator-oriented | Add a short “Artifact (paper)” section pointing here; consider `docs/research/ARTIFACT-README.md` copy for the Zenodo zip |
| `CITATION.cff` | Added | Insert DOI after Zenodo |
| Accepted paper PDF in the archive | n/a until accept | |
| Easy-to-run form (container/VM/website) | **Website yes** (Pages demos); **containerized cluster no** | Highest-leverage gap for the **demo track** (“do not expect reviewers to build your code”) |

## Functional criteria (self-score)

| Criterion | Score | Notes |
|-----------|-------|-------|
| Documented | Partial | Strong operator docs; academic “how this relates to claims C1–C5” now in this folder |
| Consistent | Partial | Paper draft cites real paths; demo videos must match the tagged release |
| Complete | Partial | Sample apps live in **other** repos — pin SHAs in the archive |
| Exercisable | Partial | `--local-only` regression is the honest 15–30 min path; full intercept E2E is not |

## Demo-track “tool” requirement (separate from AE)

ICSE Demonstrations: distribute as website, VM, or container that stays up.

| Option | Effort | Recommendation |
|--------|--------|----------------|
| GitHub Pages + existing MP4s | Already live | **Minimum** for submission: reviewers watch the 3–5 min video and skim Pages |
| Hosted Management GUI + orchestrator | Needs a durable cluster and a plan to keep it up “indefinitely” | Nice if you have spare infra; do not promise it if it will rot |
| Published Kind node image or k3d + preloaded images | One-time snapshot work | Best AE Functional path |
| “Clone and `make demo`” only | Fails CFP wording | Not sufficient as the *only* distribution |

## Reviewer-timed script (to add before AE)

A single documented path, e.g.:

```bash
# < 10 min, no cluster — supports C1 resolver + unit tests
./scripts/run-regression.sh --local-only
```

And a second path clearly marked **long**:

```bash
# cluster — supports C3; not expected of demo reviewers
./scripts/run-e2e-with-intercepts.sh --intercept-backend telepresence --skip-bootstrap
```

Do not tell artifact reviewers that Kind+Tekton+Kaniko is a “quick start.”

## Open science extras

- ORCID for the author (camera-ready).
- CodeMeta.json optional.
- Do not include `.env`, kubeconfigs, or webhook secrets in the Zenodo zip (`.gitignore` already excludes `.env`).
