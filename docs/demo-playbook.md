# Demo playbook — what to record and how to show the system

Playbook for creating **screen recordings and presentation assets** that demonstrate how the tekton-dag system works and how to use its key features. Use this to plan segments, talking points, and what to show on screen. See [milestones/milestone-8.md](../milestones/milestone-8.md) for the full milestone scope.

---

## 1. Recording checklist (what to record)

Use this as a scene list. Each segment can be one short clip or part of a longer run.

| # | Segment | What to show | Key message |
|---|---------|--------------|-------------|
| 1 | **Architecture overview** | Diagram or slide: stack (FE → BFF → API), Tekton pipelines (PR vs merge), intercept routing. | One diagram: request path + pipeline flow. |
| 2 | **Data flow + live test** | Live request from entry point through the stack; show `x-dev-session` in requests/responses; show which service handles it; trigger a real test (pipeline or curl). | Data flows through the chain; header identifies “PR” traffic. |
| 3 | **Intercept routing (PR vs normal)** | Two requests: one with header → PR build; one without → original deployment. Optional: run M6 scenario script and show output. | Same URL; header decides PR vs original. |
| 4 | **Local run + step-debug** | Run one app locally with mirrord (or Telepresence), attach IDE debugger, set breakpoint, send request with intercept header, step through code. | Develop and debug locally with real cluster traffic. |
| 5 | **Tekton Results DB** | Install Results (or show already installed), run a pipeline, query the Results API (script or API call), show run history and status. | Pipeline history is stored and queryable. |
| 6 | **End-to-end PR flow (optional)** | Open PR → pipeline runs → intercept deploys → tests pass → comment on PR; or use `run-valid-pr-flow.sh` and show key steps. | Full automation: PR → test → feedback. |

---

## 2. Segment details and key features to demo

### Segment 1: Architecture overview

- **Record:** Slide or diagram + short voice-over.
- **Show:**  
  - Stack: Frontend (Vue) → BFF (Spring Boot) → API (Spring Boot/Gradle).  
  - Pipelines: `stack-pr-test` (PR: build changed app, deploy intercept, validate, test), `stack-merge-release` (merge: promote, build, tag, push).  
  - Intercept: traffic with `x-dev-session` → PR pod; no header → original deployment.
- **Key feature:** Single slide/sketch of “how it all fits together.”

---

### Segment 2: Data flow + live test

- **Record:** Browser or Postman/curl; optionally DevTools or logs showing the header.
- **Show:**  
  1. Send request to entry point (e.g. Vue app or BFF) **with** `x-dev-session: pr-demo` (or similar).  
  2. Show the request hitting BFF then API (logs or UI).  
  3. Show the header in a downstream request or log line.  
  4. Trigger a real test (e.g. run propagation validation or M6 script) and show success output.
- **Key features:** Request path through the stack; header propagation; live test pass.

---

### Segment 3: Intercept routing (PR vs normal traffic)

- **Record:** Two curls or two browser requests; optional split screen with pipeline/deploy view.
- **Show:**  
  1. Request **without** header → response from original deployment (e.g. body or header that identifies “release” build).  
  2. Request **with** header → response from PR/local build (e.g. “LOCAL-PR-1” or custom body).  
  3. Optional: run `./scripts/run-mirrord-m6-scenarios.sh 3` and show “OK” lines for both no-header and header requests.
- **Key features:** Same URL, different backend based on header; no impact on normal traffic.

---

### Segment 4: Local run + step-debug

- **Record:** IDE (VS Code, IntelliJ, etc.) + terminal; request sent from browser or curl.
- **Show:**  
  1. Start app locally with intercept: e.g. `mirrord exec -f docs/mirrord-poc/mirrord.json -- java -jar app.jar` (or equivalent for your app).  
  2. Attach debugger (e.g. remote debug on port 5005).  
  3. Set breakpoint in the handler that serves the request.  
  4. Send request **with** intercept header from browser or in-cluster curl.  
  5. Breakpoint hits; step through a few lines; show variables/stack.
- **Key features:** App runs on your machine; cluster traffic with the right header reaches you; full step-debug with live data.

---

### Segment 5: Tekton Results DB

- **Record:** Terminal and/or browser (if you add a simple UI or use tkn/Dashboard).
- **Show:**  
  1. **Setup (if not already done):** Postgres + Tekton Results:  
     `./scripts/install-postgres-kind.sh`  
     `./scripts/install-tekton-results.sh`  
  2. **Run a pipeline** so there is history: e.g. `./scripts/generate-run.sh --mode pr --stack stack-one.yaml --app demo-fe --pr 99 --apply`, or any PipelineRun.  
  3. **Query the Results API:**  
     `./scripts/verify-results-in-db.sh`  
     (Optionally show the port-forward and curl to the Results API; see script for URL and auth.)  
  4. **Show output:** List of results (PipelineRun/TaskRun records), status, names.  
  5. Optional: Tekton Dashboard or `tkn pipelinerun list` alongside to tie “runs I see in the cluster” to “runs stored in Results.”
- **Key features:** Pipeline and task run history is persisted in Postgres; queryable via Tekton Results API; script proves data is there.

**Results API details (for narration or captions):**

- The **Watcher** writes PipelineRun/TaskRun data into the Results DB (Postgres).
- The **Results API** exposes a REST API; we port-forward and call it (or use `verify-results-in-db.sh`).
- Use case: audit trail, dashboards, integration with other tools that need run history.

---

### Segment 6: End-to-end PR flow (optional)

- **Record:** GitHub PR page + pipeline run (Dashboard or `tkn` logs) + PR comment.
- **Show:**  
  1. Open a PR in an app repo (or use existing PR).  
  2. Webhook triggers `stack-pr-test` (or trigger manually).  
  3. Pipeline: clone → build changed app → deploy intercept → validate propagation (and original traffic) → run tests.  
  4. Pipeline completes; PR comment with status/link (if configured).  
  Alternative: run `./scripts/run-valid-pr-flow.sh --app demo-fe` and show the main steps and final outcome.
- **Key features:** Single PR triggers full test; only changed app is built; intercept isolates PR traffic; automation from PR to feedback.

---

## 3. Suggested run order for a single long recording

If you want one continuous take (edit later into segments):

1. **Intro slide** — title, “tekton-dag: PR testing with intercepts and local debug.”
2. **Architecture** — Segment 1 (diagram/slide).
3. **Data flow** — Segment 2 (live request + test).
4. **Intercept routing** — Segment 3 (with vs without header).
5. **Tekton Results** — Segment 5 (install if needed, run pipeline, run verify script, show list).
6. **Local step-debug** — Segment 4 (mirrord + IDE + breakpoint).
7. **PR flow** — Segment 6 (optional; PR → pipeline → result).
8. **Outro** — “Where to learn more” (README, milestone-8, docs).

---

## 4. OBS Studio orchestration

Use **OBS Studio** to capture screen, windows, and (optionally) mic. Below: scene layout, sources, settings, and workflow so you can switch scenes in sync with the playbook segments.

### 4.1 Scenes (map to segments)

Create one scene per segment so you can switch cleanly. Name them so the list order matches the run order:

| OBS scene name       | Playbook segment | Main content |
|----------------------|------------------|--------------|
| 01 Intro             | Intro slide      | Image or browser with title slide. |
| 02 Architecture      | Segment 1        | Slide/diagram (image, PDF, or browser). |
| 03 Data flow         | Segment 2        | Browser + DevTools, or terminal + browser. |
| 04 Intercept routing | Segment 3        | Terminal (curl/script) or split: terminal + browser. |
| 05 Tekton Results    | Segment 5        | Terminal (install, pipeline, `verify-results-in-db.sh`). |
| 06 Local step-debug  | Segment 4        | IDE (e.g. VS Code) + terminal; optional second window for browser/curl. |
| 07 PR flow           | Segment 6        | Browser (GitHub PR) + Dashboard or terminal. |
| 08 Outro             | Outro            | Slide or browser with “Where to learn more”. |

**Workflow:** Start recording at the top; switch to the next scene when you move to the next segment; stop recording at the end. You can trim or split the single file later, or stop/start recording per segment if you prefer separate files.

### 4.2 Sources (what to add per scene)

- **Display Capture** — Full screen or specific monitor. Use for “everything on screen” (IDE + terminal + browser). Add to scenes 03, 04, 05, 06, 07, or use Window Capture for a single app.
- **Window Capture** — Single window (IDE, terminal, browser). Use when you want to hide other apps and avoid capturing the OBS UI. Add the relevant window to each scene; hide others or use a dedicated “demo” desktop.
- **Image** — For intro/architecture/outro slides. Add an Image source, point to `docs/demos/slides/` (e.g. `intro.png`, `architecture.png`, `outro.png`). Resize to fit canvas.
- **Browser Source** — Optional: live slide deck (e.g. Reveal.js or Google Slides URL) or a static “Now showing: …” label. Useful for 01, 02, 08.
- **Audio Input (Mic)** — Add your microphone to every scene where you narrate. Use OBS filters (Noise Suppression, Compressor) if needed.
- **Audio Output (Desktop)** — Optional: capture system audio if you want clicks or terminal sounds. Often leave disabled for clean narration.

**Tip:** Duplicate the same “terminal” or “browser” window capture across scenes, or use one Display Capture and only change what’s on screen before switching scenes.

### 4.3 Recommended OBS settings

- **Output (Recording):**
  - **Recording format:** mp4 (or mkv for safer recovery if OBS stops unexpectedly).
  - **Encoder:** Hardware if available (e.g. NVENC, AMF, Apple VT); otherwise x264.
  - **Rate control:** CBR or VBR; bitrate 8–15 Mbps for 1080p (adjust for 720p or 4K).
  - **Recording path:** e.g. `docs/demos/recordings/` or a dedicated folder; name with date or segment (e.g. `tekton-dag-demo-2026-03-05.mp4`).
- **Video:**
  - **Base resolution:** 1920×1080 (or your display). Match output to base so you don’t scale twice.
  - **Output resolution:** Same as base (1080p) unless you need 720p for file size.
  - **FPS:** 30 (or 24 for smaller files). 60 only if you need smooth cursor/animations.
- **Audio:**
  - **Sample rate:** 48 kHz. Match in Advanced Audio Properties for all sources.
  - **Channels:** Stereo.
- **Hotkeys (optional):** Assign “Start Recording” and “Stop Recording” to keys you won’t hit during the demo (e.g. F9/F10). Optionally “Switch to scene: Next” to step through scenes without clicking.

### 4.4 Before you hit Record

1. **Test all scenes** — Click each scene; confirm the right window/screen/slide is visible and not covered by OBS.
2. **Check mic level** — Talk at normal volume; green bar in OBS mixer, no red. Apply Noise Suppression if the room is noisy.
3. **Close or hide** — Notifications, other browsers, and apps you don’t want in the shot. Consider Do Not Disturb / presentation mode.
4. **Resolution** — If using Window Capture, set the app window to 1080p (or your output res) so it fills the frame without tiny text.
5. **Recording path** — Ensure the folder exists and has free space (e.g. 2–5 GB for a 15–30 min 1080p recording).

### 4.5 During the recording

- **Switch scene** in OBS when you move to the next segment (e.g. after the intro slide, switch to “02 Architecture”; when you open the terminal for data flow, switch to “03 Data flow”). Narrate as you go.
- **Pause** — OBS doesn’t have a built-in pause; either stop and start a new file for the next segment, or keep one continuous take and edit pauses out later.
- **If you flub** — Keep going; you can trim the mistake in post, or stop and restart the segment (then cut and keep the best take).

### 4.6 After recording

- **Trim / split** — Use OBS remux (if you used mkv) or a simple editor (e.g. lossless cut, ffmpeg, or your editor) to cut the single file into segment clips (e.g. `01-intro.mp4`, `02-architecture.mp4`, …) or remove dead air.
- **Export to `docs/demos/`** — Move or copy the final file(s) into the repo (e.g. `docs/demos/recordings/`) and link them from the milestone or README if desired.

---

## 5. Where to put finished assets

- **Recordings:** `docs/demos/` or `docs/demos/recordings/` (e.g. `data-flow-and-test.mp4`, `local-step-debug.mp4`, `tekton-results-db.mp4`). Set OBS recording path to this folder so files land in the repo; or record elsewhere and copy the final edits here. Host externally and link from the repo if files are large.
- **Slides:** `docs/demos/` or `docs/presentations/` (e.g. `tekton-dag-demo.pptx` or `demo-deck.md`).
- **Playbook:** This file — `docs/demo-playbook.md` — linked from [milestone-8](../milestones/milestone-8.md).

---

## 6. References

- [Milestone 8](milestones/milestone-8.md) — demo scope and success criteria.
- [Quick start (README)](../README.md#quick-start-local) — setup (including optional Postgres + Tekton Results).
- [Mirrord PoC results](mirrord-poc-results.md) — config and how to run mirrord.
- [Mirrord M6 test scenarios](mirrord-m6-test-scenarios.md) — in-cluster test procedures.
- [.vscode/README.md](../.vscode/README.md) — launch configs for local run and debug.
- `scripts/install-tekton-results.sh` — install Results.
- `scripts/verify-results-in-db.sh` — query Results API (list runs).
