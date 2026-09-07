# SEIP submission backlog (no this-cycle deadline)

**Stance.** Do **not** aim at ICSE 2027 dates (SEIP paper due 23 Oct 2026). Other work comes first. This file is the standing bar for a later **Software Engineering in Practice** cycle (ICSE 2028 or equivalent FSE/ASE industry track). The requirements below are the CFP shape, not a calendar.

**What this is not.** Not a tool-demo 4-pager. Not a research-track experiment (baselines, p-values). SEIP wants a **practical problem, investigated in a real context, with evidence for the conclusions**, plus insights a practitioner could use.

**How to iterate.** Pick **one** unchecked slice (a single `Sxx` id). Land it. Stop. Do not open the next slice in the same sitting unless it is a one-line fix. Each slice should be mergeable without a named conference deadline.

Related: [evaluation.md](evaluation.md) (what tests actually prove), [contributions.md](contributions.md) (claims allowed today), [gaps.md](gaps.md) (workshop leftovers, not SEIP).

---

## Gate 0 — industrial context (blocks the paper, not the engineering)

SEIP submissions without a **site** read as product READMEs. Kind + six first-party sample repos is not a site.

Fill [seip/context-memo.md](seip/context-memo.md) before writing evaluation prose.

- [ ] **S00** Decide the site: named org, anonymized org (“Company A, ~N services”), or *this platform as the author’s own multi-repo practice* (weaker; only viable if you have real PR/PipelineRun history, not only `stack-one` on Kind).
- [ ] **S01** Record: languages, service count, how CI worked *before*, who operates the cluster, what a “PR” means there.
- [ ] **S02** Legal / comms: what may be named, what must be redacted, whether PipelineRun logs and interview notes can leave the building.
- [ ] **S03** Go / no-go: if S00–S02 cannot be answered, **do not write an SEIP paper**. Keep improving the artifact (Workstream C). A tool demo remains valid; SEIP does not.

---

## Workstream A — Problem from practice

CFP: *a problem of practical importance* and *in what context it was investigated*.

- [ ] **S10** Write the pre-tool pain in one page using **only** site facts: duplicated pipelines per stack, preview-namespace cost, header drop on a polyglot hop, intercept stealing baseline traffic, etc. No architecture lecture.
- [ ] **S11** Attach 3–8 concrete incidents or tickets (redacted): date, what broke, who felt it. Session notes in this repo are seeds, not substitutes for site incidents.
- [ ] **S12** State what “success” meant for the site *before* any metric collection (e.g. “PR for a mid-tier service must not clone the stack; unmatched traffic must stay on baseline”).

---

## Workstream B — Evidence from that site

CFP: *how the problem was investigated* and *evidence for the conclusions*. Empty tables fail SEIP.

Pick a **window** (for example several months of operation) and freeze it. Do not mix Kind PoC numbers into production tables.

- [ ] **S20** Export PipelineRun outcomes for the window: counts by pipeline (`bootstrap` / `pr` / `merge` / `promote`), success vs fail, wall-clock. Script + CSV in `docs/research/seip/data/` (git-lfs or Zenodo later if large).
- [ ] **S21** Isolation log: for intercept PRs, unmatched-traffic probes and matched-traffic probes (pass/fail). If production cannot probe, run the same probes on a **staging fleet that the site actually uses**, and say so.
- [ ] **S22** Cost or capacity: node-minutes, namespace count, or image-build count **before vs after** intercept-style PRs — even a coarse ops estimate with a documented method. “It felt cheaper” is not evidence.
- [ ] **S23** Optional but strong: 6–12 short developer interviews or a short survey on the PR/debug path. ACM human-subjects policy applies; if you skip this, say why in threats.
- [ ] **S24** Negative results: intercept privilege vs Pod Security, registry topology (Kind `localhost:5000` vs `5001`), stdout pollution in batch waits, webhook fail-open vs fail-closed. SEIP papers that never fail look like ads.
- [ ] **S25** Threats paragraph drafted from the actual window: author = platform owner, one cluster, toy vs real apps, construct (HTTP routing ≠ data isolation).

**Done for B:** a reviewer can see *where the numbers came from* and could in principle re-run the export script on a similar cluster.

---

## Workstream C — Artifact credibility (supports the paper; does not replace B)

Reviewers will clone GitHub. A green local suite that Actions never runs undermines “we operate this in practice.”

Each slice is independently useful even if Gate 0 is still open.

- [ ] **S30** GitHub Actions workflow: `run-regression.sh --local-only` on pull requests (Phase 1 + pytest + vitest). Badge or README line that cites **CI**, not milestone tables.
- [ ] **S31** Add Java (`mvn test` in both baggage modules) and PHPUnit to that same driver or a second CI job.
- [ ] **S32** Add `go test ./internal/...` for `operator/`.
- [ ] **S33** Nightly or manual cluster job: Playwright + Newman + `stack-dag-verify`. Record a log on a tagged release; do not pretend every PR ran Kind.
- [ ] **S34** On a chosen tag: `run-e2e-with-intercepts.sh` for Telepresence **and** mirrord; attach logs to the release.
- [ ] **S35** Refresh README / milestone test counts from CI (orchestrator is already 105 pytest, not 62).
- [ ] **S36** License + `CITATION.cff` already landed; add a Zenodo DOI when you freeze a “paper artifact” tag (any year).

C can proceed indefinitely around other jobs. It is **necessary for trust**, not sufficient for SEIP.

---

## Workstream D — Paper (only after S03 = go)

Target shape (typical ICSE SEIP): **10 pages** main text + **2 pages** references, IEEE `IEEEtran` `10pt,conference`, **single-anonymous** (org and authors visible). Confirm the CFP of the *year you submit*.

Section map — fill in this order so you do not write architecture before evidence:

| § | Content | Feeds from |
|---|---------|------------|
| 1 | Problem + contributions in *practice* language | S10, S12 |
| 2 | Industrial context | S00–S02 |
| 3 | Approach as deployed (stack DAG, roles, intercepts) — short | [contributions.md](contributions.md), keep to what the site used |
| 4 | Investigation method (window, data sources, probes) | S20–S23 |
| 5 | Results | CSVs from B |
| 6 | Lessons learned | S24, [seip/lessons-learned.md](seip/lessons-learned.md) |
| 7 | Related work (practice + research) | [related-work.md](related-work.md) |
| 8 | Threats | S25 |
| 9 | Conclusion + what you would not do again | |

- [ ] **S40** New `docs/research/paper-seip/main.tex` (do not stretch the 4-page tool draft). Outline-only first: headings + bullet evidence pointers, no filler.
- [ ] **S41** Expand §1–2 from the context memo. No metrics yet if B is incomplete — leave `[DATA]` markers.
- [ ] **S42** Expand §3 only for mechanisms **the site actually ran**. Optional operator / M13 leftovers stay in “status,” not as claims.
- [ ] **S43** Expand §4–5 when CSVs exist. Every number has a row in `seip/data/`.
- [ ] **S44** Expand §6 from `lessons-learned.md` (failures first).
- [ ] **S45** Related work + threats + ORCID/affiliation + IEEE/ACM AI disclosure.
- [ ] **S46** Page-budget pass: ≤10+2, no font tricks. Compile twice. Equalize last page columns.

---

## Workstream E — Submission hygiene (when a CFP is chosen)

Do this only when you have picked a specific year/track. Not now.

- [ ] **S50** Confirm page limit, template, HotCRP, single- vs double-anonymous, concurrent-submission rules.
- [ ] **S51** Do not dual-submit the same PDF as a tool demo / workshop paper.
- [ ] **S52** Optional artifact evaluation after accept (Zenodo + reviewer-timed path).
- [ ] **S53** Camera-ready: ORCID, copyright, presentation registration.

---

## Suggested iteration order (when a slice of time appears)

1. **S00–S03** if you have even a short window with the site — or skip SEIP and stay on the artifact (C).
2. **S30** when you next touch GitHub Actions anyway.
3. **S11 / S24 / lessons-learned** whenever you hit a real incident; one paragraph per incident is enough.
4. **S20–S22** once a metrics window exists (needs the site or a real staging fleet).
5. **S40+** last. Prose without B is what gets rejected.

---

## “Complete SEIP-compliant submission” — done criteria

All of the following, not a subset:

1. Gate 0 is **go**, and the paper names the context at the agreed disclosure level.
2. At least one **quantitative** practice result (S20 or S22) and one **isolation** result (S21), each with method.
3. At least three **lessons that hurt** (S24), not only successes.
4. Threats that match the claims (S25).
5. IEEE PDF within that year’s page cap; affiliations visible; AI disclosure if required.
6. Artifact URL + license; CI that actually ran on the tagged commit (S30 at minimum).
7. Related work that includes preview environments, intercept tools, and CI-at-scale papers — not only vendor docs.

Until then, the honest public claim is: **functional platform + local tests**, packaging for a later practice paper.
