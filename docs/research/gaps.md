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

## Should-do to raise the *research* bar (not required for a tool workshop)

From [`evaluation.md`](evaluation.md): intercept vs. namespace-clone cost, concurrent PR isolation, developer study, TIA comparison. Any one of these can become the core of a later SEIP or research paper; stuffing them as unsourced claims into the 4-pager will hurt.

## Must-do for a defensible “tests are done” story

Engineering completeness is separate from the HotCRP PDF. As of this branch:

- `--local-only` regression **passes** (Phase 1 + 230 pytest + 15 vitest).
- GitHub Actions does **not** run that suite on pull requests.
- Java, PHP, servlet, operator Go, Playwright (on `--local-only`), Newman, Phase 2, and intercept E2E are **out of band**.
- README milestone test counts are **stale**.

Until a PR workflow runs `--local-only` and a recorded cluster log exists for the tagged release, do not tell reviewers the platform is continuously verified.

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
