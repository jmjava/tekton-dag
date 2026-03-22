# Demo segments — M12.2 extension (regression + Management GUI)

Shot list and narration beats for **new** videos (or M8 pipeline add-ons). Produce assets with the same toolchain as [milestone-8.md](../../milestones/milestone-8.md) (`docs/demos/generate-all.sh`, Manim/TTS/ffmpeg as configured).

**Current shipped visuals (12–14):** `compose.sh` uses **Manim** (same style as segments 01–11): `RegressionSuiteScene`, `ManagementGUIArchitectureScene`, and `GUIExtensionScene` in [`animations/scenes.py`](animations/scenes.py). Render with `manim -qm scenes.py <SceneName>` (or `generate-all.sh`); outputs land under `animations/media/videos/scenes/720p30/*.mp4`. Optional: full **screen recordings** or **`vhs:`** from `terminal/12–14*.tape` if you swap `VISUAL_MAP[12–14]`.

## Segment A — Full regression walkthrough (~3–5 min)

| Beat | Visual | Narration idea |
|------|--------|----------------|
| Intro | Title card / repo README regression line | “We verify the repo in layers — not only unit tests.” |
| Local fast path | `run-regression-stream.sh --local-only` (short clip or skip if redundant) | “Without a cluster, Phase 1 and pytest still catch DAG and code bugs.” |
| Full run | `run-regression-agent.sh` or `--cluster --require-dag-verify` | “With a cluster, we require a real `stack-dag-verify` PipelineRun to succeed.” |
| Log highlights | Scroll: Phase 2 PASSED, Newman passed, optional Results | “Newman hits the orchestrator; Phase 2 proves Tekton resolve matches our CLI.” |
| Outro | `regression exit code: 0` | “Green here means the scripted bar is cleared for release or doc updates.” |

**Assets to add after recording:**

- `docs/demos/recordings/12-regression-suite.mp4` (suggested name; **do not reuse** `09-results-db`)  
- Narration stub: [narration/12-regression-suite.md](narration/12-regression-suite.md)  
- Update `docs/index.html` with a new card when the MP4 exists.  
- Optional: `docs/demos/audio/12-regression-suite.mp3` + `timing.json` entry if using M8 automation.

## Segment B — Management GUI architecture (~2–4 min)

| Beat | Visual | Narration idea |
|------|--------|----------------|
| Stack | Simple diagram: Browser → Vue → `/api` → Flask → Kubernetes | “No cluster credentials in the browser.” |
| Router + views | Quick pan: Trigger, Monitor, DAG in dev server | “Each view maps to operator workflows.” |
| Team scope | Team switcher + Network tab showing `/api/teams/...` | “The active team prefixes API calls.” |
| DAG | `DagView` with Vue Flow | “Graph comes from stack YAML resolved server-side.” |

**Companion doc:** [MANAGEMENT-GUI-EXTENSION.md](../MANAGEMENT-GUI-EXTENSION.md)  
**Narration stub:** [narration/13-management-gui-architecture.md](narration/13-management-gui-architecture.md)  
**Recording:** e.g. `docs/demos/recordings/13-management-gui-architecture.mp4`

## Segment C — Extending the GUI for more Tekton (~2–3 min)

| Beat | Visual | Narration idea |
|------|--------|----------------|
| Pattern | Split: `pipelines.py` + `runs.js` side-by-side | “New surface: add Flask route, then Pinia + view.” |
| Checklist | Bullet list on slide (from extension doc) | “Tests: pytest for API, Playwright for UI.” |
| Example idea | Optional: mock “TaskRun logs” feature | “Backend streams logs; frontend shows a modal — same pattern for Results or Triggers.” |

**Narration stub:** [narration/14-gui-tekton-extension.md](narration/14-gui-tekton-extension.md)  
**Recording:** e.g. `docs/demos/recordings/14-gui-tekton-extension.mp4`

## Cross-links

- Narrative testing story: [TESTING-AND-REGRESSION-OVERVIEW.md](../TESTING-AND-REGRESSION-OVERVIEW.md)  
- Operator commands: [REGRESSION.md](../REGRESSION.md)  
- Playbook table: add rows to [demo-playbook.md](../demo-playbook.md) §1 when segments are recorded.
