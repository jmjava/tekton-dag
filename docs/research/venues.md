# Venue map (ICSE 2027 and related)

Dates below are taken from the ICSE 2027 researchr pages (AoE). Confirm on the track site before submitting; ICSE sometimes shifts workshop paper dates.

**Conference:** ICSE 2027, Dublin, Ireland, 25 April – 1 May 2027.  
**Uniform workshop paper deadline (IEEE companion):** 13 November 2026 (some workshop sites still list 27 November — use the date on *that* workshop’s CFP). Notification 11 December 2026. Camera-ready 29 January 2027.

## Recommended order

| Priority | Venue | Why it fits this repo | Why it might reject | Deadline |
|----------|-------|----------------------|---------------------|----------|
| **1** | [ICSE Tool Demonstration and Data Showcase](https://conf.researchr.org/track/icse-2027/icse-2027-demonstrations) | Working system, 18 narrated demo segments, public GitHub + Pages. 4-page IEEE paper + 3–5 min YouTube video. Single-anonymous (authors visible). Artifact eval optional after accept. | Reviewers must not have to *build* the system; they expect a website, container, or VM. Novelty of “underlying ideas” is scored. A 45-minute concat is the wrong video. | **23 Oct 2026** |
| **2** | [SESoS 2027](https://conf.researchr.org/home/icse-2027/sesos-2027) (15th IEEE/ACM Workshop on Software Engineering for Systems-of-Systems and Software Ecosystems) | A stack is a software ecosystem: independently versioned apps, shared platform, polyglot teams. CFP explicitly lists *continuous engineering*, *V&V tools*, *industrial experience*, *platform governance*. Short papers ≤4 pages or research ≤8. Journal SI invitation possible (ASE journal). | Must speak SoS/SECO language (constituents, independence, emergent routing behavior), not “here is our CI product.” | **13 Nov 2026** (confirm on workshop site) |
| **3** | [IDE Workshop 2027](https://ide-workshop.github.io/) (4th International Workshop on IDEs) | Local-debug path (mirrord / Telepresence + VS Code launch configs) is a clean slice. | Only covers a *subset* of the contribution. Submit only if the demo track is declined and you narrow the paper to IDE-integrated intercept debugging. | **27 Nov 2026** (workshop site) |
| **Avoid as first paper** | [ICSE SEIP](https://conf.researchr.org/track/icse-2027/icse-2027-seip) | Would be the right *later* venue with an industrial deployment story. | Reviewers expect a named problem in a real organization, investigation method, and evidence for conclusions. This repo is currently a Kind/PoC + sample apps, not a case study. Same deadline as demos (**23 Oct 2026**), 10+2 pages. | 23 Oct 2026 |
| **Avoid as first paper** | ICSE Research Track | Release engineering / DevOps is in-scope. | Needs a research question, related-work gap, and empirical method that a 4-page tool paper cannot carry. | (earlier; typically ~Mar–Sep 2026 — check if still open) |
| **Weak / stretch** | [SERS 2027](https://conf.researchr.org/home/icse-2027/sers-2027) (Software Engineering and Research Software) | 4-page extended abstracts on SE for *research software*. | tekton-dag is a CI platform, not research software (RSE). Only fits if reframed as “SE tooling used to maintain this research artifact,” which is circular. | workshop uniform date |
| **Weak / stretch** | [DTwiSE 2027](https://conf.researchr.org/home/icse-2027/dtwise-2027) | CFP lists DevOps / CSE. | Digital-twin workshop; grafting “stack DAG = twin of production” is a stretch unless you actually model runtime twins. | 13 Nov 2026 |
| **Out of scope as primary** | ChainSEC, AGENT, LLM4Code, GREENS, etc. | Possible *mention* (supply-chain secrets, agent regression loop). | Wrong community for the main claim. | — |

Do **not** submit the same paper to the Demonstrations track and a workshop. IEEE/ACM concurrent-submission policy applies. A demo paper and a *distinct* SESoS experience/short paper (different claims, different text) can coexist if the overlap is small and each cites the other as complementary; that is a later decision.

## What “workshop submission status” means here

A workshop PC typically checks:

1. **Problem in the community’s vocabulary** (SoS/SECO, release engineering, developer tools).
2. **A contribution that is not a blog post** — model, method, or evaluated tool.
3. **Related work that names prior systems** (Tekton, GitHub Actions DAGs, preview environments, Telepresence, Istio, test-impact analysis).
4. **Evidence proportional to claims** — a tool paper may use a worked example + functional validation; a research paper may not.
5. **An artifact others can cite** — license, URL, preferably DOI.
6. **IEEE formatting** — `\documentclass[10pt,conference]{IEEEtran}`, page cap **inclusive of references** (no extra pages).

This packaging aims at (1)–(6) for a **tool / short workshop** paper. It does **not** claim SEIP or research-track readiness.

## ICSE Demonstrations — submission checklist (from the CFP)

Must include:

- 4-page IEEE PDF (title 24pt, body 10pt, IEEEtran, **no** `compsoc`).
- URL of a **3–5 minute YouTube** video in the abstract.
- Link to a **publicly available tool** and usage instructions (repo optional if OSS).
- Distribution in an easy-to-use form: website, VM, or container. *“Do not expect reviewers to have to build your code.”*
- Envisioned users, SE challenge, user workflow, validation results **or** planned study design.

Evaluation criteria include novelty of underlying ideas, video quality, usefulness, and related literature.

After accept: optional [Artifact Evaluation](https://conf.researchr.org/track/icse-2027/icse-2027-artifact-evaluation) (register 22 Jan 2027, submit 29 Jan 2027) for Available / Functional / Reusable badges. GitHub alone does **not** qualify for **Available**; need Zenodo/Software Heritage DOI. See [artifact-checklist.md](artifact-checklist.md).

## Suggested titles (pick one voice)

| Voice | Title |
|-------|--------|
| Tool demo | Tekton-DAG: Stack-Aware Pull-Request Isolation for Polyglot Microservice Ecosystems |
| SESoS | Isolating Change in a Software Ecosystem: A Stack-DAG Approach to Preview Traffic |
| IDE (narrow) | Header-Matched Intercepts for In-IDE Debugging of In-Cluster Microservice Graphs |

The LaTeX draft uses the tool-demo title.
