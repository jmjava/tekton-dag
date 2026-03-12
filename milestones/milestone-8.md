# Milestone 8: Demo assets — data flow + live tests + local step-debug

> **Planned.** Follows [milestone 7](milestone-7.md) (deploy-intercept-mirrord). Produces presentation and recording assets to demonstrate the system and the developer experience of running and debugging an app locally against the live environment.

## Goal

Prepare **PowerPoint (or equivalent) and/or screen recordings** that show:

1. **Data flow through the system** — with live tests: request path (e.g. Frontend → BFF → API), header propagation (`x-dev-session`), and how intercept routing steers PR traffic to the right place.
2. **Step-debug when running the app locally** — run one app locally (e.g. BFF) with mirrord (or Telepresence), attach a debugger (IDE breakpoints), and show that requests carrying the intercept header hit the local process so you can step through code in real time while the rest of the stack runs in the cluster.

Success = reusable demo materials for stakeholders and teams, plus a clear “local dev + debug” story.

---

## Audiences

- **Stakeholders / management** — high-level data flow, value of PR testing and intercepts.
- **Developers** — how to run one service locally, attach a debugger, and receive real traffic from the cluster (step-debug with live environment).

---

## Deliverables

### 8.1 Data flow + live test recording(s)

- **Content:** End-to-end request path through the stack (e.g. Vue → Spring Boot BFF → Spring Boot API), with `x-dev-session` (or equivalent) shown in requests/responses.
- **Live test:** Trigger a real test (e.g. from the PR pipeline or manual curl/Postman) and show in the recording: which service handles the request, that the header is forwarded, and that intercept routing sends “PR” traffic to the PR build and “normal” traffic to the deployed app.
- **Format:** Screen recording (and optionally a slide deck) that can be replayed in meetings or linked from the repo.

### 8.2 Local run + step-debug recording

- **Content:** Developer runs one app (e.g. BFF) **locally** with mirrord (or Telepresence), with the same `header_filter` / intercept header used in the pipeline.
- **Demo steps:**
  1. Start the app locally (e.g. `mirrord exec -f config.json -- java -jar app.jar` or equivalent for the stack).
  2. Attach the IDE debugger (e.g. Java remote debug, or Node/Python debugger).
  3. Set a breakpoint in the code path that handles the request.
  4. Send a request (from browser, curl, or another service in the cluster) that includes the intercept header.
  5. Show that the request hits the local process and the breakpoint fires — **step through the code** to demonstrate full step-debug against the live environment.
- **Format:** Screen recording with voice-over or captions; optional short slide deck (e.g. “Local dev with cluster context” and “Step-debug with live traffic”).

### 8.3 Optional: PowerPoint (or Markdown) deck

- **Content:** Slides summarizing (1) architecture, (2) data flow and header propagation, (3) intercept behavior (PR vs normal traffic), (4) local run + step-debug workflow.
- **Location:** e.g. `docs/demos/` or `docs/presentations/` in the repo, or linked from the milestone doc.

### 8.4 Demo playbook

- **[docs/demo-playbook.md](../docs/demo-playbook.md)** — Playbook for what to record and how to demo key features: segment list (architecture, data flow, intercept routing, local step-debug, **Tekton Results DB**, optional end-to-end PR flow), suggested run order, and where to put assets. Use it to plan recordings and touch on the Results DB (install, run pipeline, query via `verify-results-in-db.sh`).

### 8.5 Documentation

- **Where to put assets:** e.g. `docs/demos/` (recordings, slide exports, links to external hosting if needed).
- **How to run the demos:** Short guide (or link to existing mirrord/Telepresence and stack docs) so someone can reproduce the data-flow and local-debug demos.

---

## Success criteria

- [ ] At least one screen recording showing **data flow + live test** (request path, headers, intercept behavior).
- [ ] At least one screen recording showing **local run + step-debug** (app running locally, debugger attached, breakpoint hit with live traffic).
- [ ] Demo assets (and optional deck) documented and linked from this milestone or README.
- [ ] README or docs updated to point to the demo assets and “how to run the demo” steps.

---

## Technical notes

- **Local step-debug:** Works because the intercept tool (mirrord or Telepresence) sends matching traffic to the **local process**. The app runs in the IDE (or terminal) with a debugger attached; no need to debug inside the cluster.
- **Stack choice:** Use the same stack and namespace as in M5/M6 (e.g. `staging`, `release-lifecycle-demo`, `demo-api`). Configs under `docs/mirrord-poc/` can be reused or slightly adapted for the demo (e.g. `x-dev-session: demo` for a single demo session).
- **Tools:** mirrord CLI (`./scripts/install-mirrord.sh`), IDE debugger (e.g. VS Code, IntelliJ), and a way to send requests (browser, curl, or in-cluster test pod).

---

## Non-goals

- Recording every possible framework (one clear example is enough).
- Building new tooling; use existing mirrord/Telepresence and pipeline docs.

---

## References

- [Milestone 5](milestone-5.md) — mirrord PoC, config, security.
- [Milestone 6](milestone-6.md) — validated scenarios, in-cluster tests.
- [docs/mirrord-poc-results.md](../docs/mirrord-poc-results.md) — config format, how to run mirrord.
- [docs/mirrord-m6-test-scenarios.md](../docs/mirrord-m6-test-scenarios.md) — test procedures.
