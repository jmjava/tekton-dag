# Academic packaging (workshop / tool-demo readiness)

This folder organizes the **existing** tekton-dag engineering work so it can be reviewed as a software-engineering **artifact + paper**, not as a product changelog.

It does **not** invent a new platform and it does **not** drive design. Architecture lives in milestones, Helm, `operator/`, and `scripts/`. This tree maps what shipped onto reviewer-shaped documents: claimed contributions, related work, evaluation evidence, threats, citation. If product work and a paper claim list disagree, **change the paper**, not the platform.

## Current status

| Bar | Status | Notes |
|-----|--------|-------|
| **Workshop / tool-demo paper** | Draft | IEEE 4-page skeleton in [`paper/`](paper/) — retargetable to ICSE Demonstrations or a co-located workshop |
| **Open license** | Done | Apache-2.0 at repo root [`LICENSE`](../../LICENSE) |
| **Citation metadata** | Done | [`CITATION.cff`](../../CITATION.cff) |
| **Contribution claims** | Draft | [`contributions.md`](contributions.md) — honest about engineering vs. research novelty |
| **Related work** | Draft | [`related-work.md`](related-work.md) + [`paper/refs.bib`](paper/refs.bib) |
| **Multi-repo artifact map** | Draft | [`artifact-map.md`](artifact-map.md) |
| **Evaluation evidence** | Partial | [`evaluation.md`](evaluation.md) — PR CI is `--local-only`. Cluster job exists ([cluster-regression.yml](../../.github/workflows/cluster-regression.yml)) but is **not** on PRs; no site study |
| **ACM artifact badges** | Partial | [`artifact-checklist.md`](artifact-checklist.md) — Available is blocked until Zenodo/Software Heritage DOI; Reusable needs a reviewer-timed Kind path |
| **SEIP / full research track** | Not this cycle | Standing backlog: [seip-tasks.md](seip-tasks.md). Gate 0 is industrial context. No ICSE 2027 deadline. |

**Short answer: no, the testing work is not “all done.”** Local unit/static tests are PR-gated. Cluster Kind CI is nightly/manual. Intercept E2E and comparative studies are not gated.

See [`evaluation.md`](evaluation.md) for counts from a live `--local-only` run.

## How to use this folder

1. Read [`venues.md`](venues.md) and pick a **single** first target (do not dual-submit overlapping papers).
2. Treat [`contributions.md`](contributions.md) as the claim list the paper is allowed to make.
3. Fill remaining gaps in [`gaps.md`](gaps.md) before camera-ready / artifact evaluation.
4. Compile the paper: `cd docs/research/paper && make`.
5. For a demo track: cut a 3–5 minute YouTube walkthrough from the existing [GitHub Pages segments](https://jmjava.github.io/tekton-dag/) (architecture + intercept routing + PR pipeline). Do **not** submit the 45-minute concat as the review video.

## Documents

| Document | Purpose |
|----------|---------|
| [venues.md](venues.md) | ICSE 2027 tracks/workshops, deadlines, fit, and what each venue will reject |
| [contributions.md](contributions.md) | C1–C5 claims mapped to code and docs |
| [artifact-map.md](artifact-map.md) | This repo + sample apps + docgen as one research artifact |
| [related-work.md](related-work.md) | Positioning vs. CI DAGs, preview envs, intercepts, TIA, baggage |
| [evaluation.md](evaluation.md) | What we can cite today vs. what reviewers will ask for |
| [artifact-checklist.md](artifact-checklist.md) | ACM badges + ICSE demo “easy-to-use tool” requirements |
| [gaps.md](gaps.md) | Remaining work before a workshop/tool-demo is review-ready |
| [seip-tasks.md](seip-tasks.md) | Iterable SEIP backlog (no this-cycle deadline): context gate, evidence, CI, paper |
| [paper/](paper/) | IEEE `IEEEtran` draft + BibTeX |

Engineering sources of truth remain where they are: [README](../../README.md), [DAG-AND-PROPAGATION.md](../DAG-AND-PROPAGATION.md), [milestones](../../milestones/), [REGRESSION.md](../REGRESSION.md). This folder **cites** those documents; it does not replace them.

## Author metadata to confirm before submission

Update these before HotCRP upload (they are placeholders where marked):

- Affiliation and country
- ORCID iD ([ICSE requires ORCID at camera-ready](https://conf.researchr.org/track/icse-2027/icse-2027-demonstrations))
- Whether any employer/customer may be named (needed for SEIP; not required for a tool demo)
- Generative-AI disclosure text (IEEE/ACM policy; a stub is in the paper acknowledgements)
