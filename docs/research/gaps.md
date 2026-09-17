# Gaps before a submission is review-ready

Organizing the repo (this folder, license, citation, paper skeleton) is **necessary** for workshop status. It is **not** sufficient. Remaining work is listed in submission order.

## Must-do for ICSE Demonstrations (23 Oct 2026)

1. **3–5 minute YouTube video**  
   Cut from existing segments 01 (architecture), 04 (PR pipeline), 05 (intercept routing). Voice-over must match on-screen content ([AGENTS.md](../../AGENTS.md) demo rules). Upload unlisted YouTube; put URL at end of abstract. Do **not** submit the 30–45 min concat.

2. **Retarget and freeze the 4-page PDF**  
   Compile [`paper/main.tex`](paper/main.tex), fill affiliation/ORCID, trim to ≤4 pages including references. Every claim in the PDF must appear in [`contributions.md`](contributions.md).

3. **Tag a release** (`v0.1.0-workshop` or similar) and quote that tag in the paper. Pin sample-repo SHAs in [`artifact-map.md`](artifact-map.md).

4. **Author-visible metadata**  
   Affiliation, ORCID, whether the work is independent or employer-backed (demo track is single-anonymous).

5. **IEEE/ACM AI disclosure**  
   If generative tools drafted or substantially edited the paper, disclose in acknowledgements (stub already in `main.tex`).

## Must-do for SESoS short paper (Nov 2026)

1. Rewrite the introduction in **SoS/SECO terms**: independent constituents (app repos), shared platform (tekton-dag), emergent behavior (header-matched routing).
2. One **experience** subsection: what broke when intercepts met Pod Security / Results RBAC / parallel Kaniko (session notes already mention these — turn them into lessons, not a diary).
3. Do not dual-submit the same PDF as the demo paper.

## Should-do for artifact badges (Jan 2027, after accept)

1. Zenodo DOI of the tagged release → **Available**.
2. Reviewer VM or preloaded Kind image → **Functional**.
3. Re-run `--local-only` regression on a clean machine and paste the log summary into the AE abstract.

## SEIP (not aimed at this cycle)

See **[seip-tasks.md](seip-tasks.md)**. No ICSE 2027 date. Gate 0 is a real site; Workstream C (CI) can still proceed around other work.

## Must-do for a defensible “tests are done” story

Engineering completeness is separate from the HotCRP PDF. As of this branch:

- `--local-only --require-lang-tests` **passes** and is **gated** by [`.github/workflows/local-regression.yml`](../../.github/workflows/local-regression.yml).
- Playwright, Newman, Phase 2, and Kind isolation **measurements** are gated by [`.github/workflows/cluster-regression.yml`](../../.github/workflows/cluster-regression.yml) (nightly / dispatch / `v*` tags / Helm-or-cluster-script PRs — **not** every PR). Isolation-eval is skipped on those PRs.
- Intercept E2E automation is [`.github/workflows/intercept-e2e.yml`](../../.github/workflows/intercept-e2e.yml) (weekly + path filters). Live matrix evidence is still required ([M17.3](../../milestones/milestone-17.md)).
- README milestone test counts were refreshed in the 2026-09 documentation review (orchestrator 108, common 89, GUI backend 68, Playwright 70, Newman 20/38).

Until a **recorded** cluster-regression artifact exists for a tagged commit, do not tell reviewers the *platform* (Tekton/intercepts) is continuously verified on every PR. Local unit/static CI plus scheduled Kind jobs is the honest claim.

**Kind cluster-ci design debt (2026-09-07 run, not site evidence):**

| Id | Finding | Status |
|----|---------|--------|
| **S38** | `install-tekton.sh` tracked `latest`; v1.6 rejected `taskRef.name: $(params.pre-build-task)`. Hooks use cluster resolver; pin Pipelines/Triggers. | Landed |
| **S39** | `common.sh` defaulted host `localhost:5001` while `kind-with-registry.sh` listens on **`:5000`**. Newman image push failed (`connection refused` on 5001). Phase 2 `stack-dag-verify` **Succeeded**. | Landed |
| **S33 local** | `run-cluster-ci.sh` on this Cloud Agent Kind: isolation 6/6, Phase 2 Succeeded, Newman 18 req / 36 asserts. `kind load` overlayfs warning (nested Docker); registry pull worked. | Local log (2026-09-07); GHA cluster-regression now exists as a nightly/path-filtered workflow |
| **M14 soak** | Default-on: Helm `operator.enabled=true`, Kind `STACKRUN_VIA_CRD=true`. Newman 18/18 and 6/6 StackRun → PipelineRun. Team `default` Ready; Stacks `valid` + `injectionNamespace`. Some PRs then `CouldntGetTask` (task catalog). | Landed (product); GHA cluster-regression is the scheduled proof path |
| **M15** | Idempotent StackRun→PipelineRun, GHA `--skip-operator`, Triggers `prNumber`, Flask/GUI promote wait, soak `ready==total`. | Landed [#19](https://github.com/jmjava/tekton-dag/pull/19) — [milestone-15.md](../../milestones/milestone-15.md) |
| **M16** | Team CR overlay, `continueFrom`, Kind webhook installer, escape hatches retired, spoken demos 01/08/18/19 rebuilt. | Code-complete [#20](https://github.com/jmjava/tekton-dag/pull/20)–[#24](https://github.com/jmjava/tekton-dag/pull/24); intercept follow-on is M17.3 — [milestone-16.md](../../milestones/milestone-16.md) |
| **S34 / M17.3** | Phase 2 ≠ intercept E2E. Dummy isolation-eval ≠ Telepresence/mirrord. Weekly `intercept-e2e.yml` exists; live matrix evidence still required. | Automation in-tree; checkbox open until a retained artifact |
| Lessons | Dual-port registry, Kaniko stdout vs results, intercept vs Pod Security: see [seip/lessons-learned.md](seip/lessons-learned.md). | Registry default paid in S39; intercept PSS still tracked with M17.3 |

## Must-not-do

- Cite hallucinated papers; every key is in [`paper/refs.bib`](paper/refs.bib).
- Claim industrial deployment or user-study results that are not in [`evaluation.md`](evaluation.md).
- Point reviewers at `run-regression-agent-full.sh` as the demo.
- Change demo narration without `docgen rebuild-after-audio` (repo rule).
- Promise a public always-on cluster you will not maintain.

## Suggested calendar (working backward from 23 Oct 2026)

| When | Output |
|------|--------|
| Now | This packaging merged; paper compiled locally |
| Tag + Pages check | Release matches demo site |
| Video cut | 3–5 min YouTube |
| Paper freeze | PDF ≤4 pages, bib checked |
| 23 Oct 2026 | Demo HotCRP (`icse27demos.hotcrp.com`) |
| If accepted | AE abstract 22 Jan 2027; camera-ready 20 Jan 2027 |
| 13 Nov 2026 | Optional distinct SESoS short paper |
