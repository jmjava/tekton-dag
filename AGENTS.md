# Agent instructions (tekton-dag)

## Regression — iterate until complete

Full **`run-regression*.sh`** is a **system / integration** suite for this repo (cluster-backed tiers optional). It is **not** the same as “every test on every application pull request” — see [docs/REGRESSION.md](docs/REGRESSION.md) for PR vs platform scope.

Do **not** stop after a single partial test run. Follow **[docs/AGENT-REGRESSION.md](docs/AGENT-REGRESSION.md)**:

- Run **`bash scripts/run-regression-agent.sh`** (or **`run-regression-agent-full.sh`** if Results + DB must pass).
- **Loop**: fix failures → re-run until **`regression exit code: 0`** and done criteria in the doc are met.

## Quick commands

| Intent | Command |
|--------|---------|
| Best effort for current env | `bash scripts/run-regression-agent.sh` |
| Strict + Tekton Results | `bash scripts/run-regression-agent-full.sh` |
| Timestamped log + correct exit code | `bash scripts/run-regression-stream.sh …` |

Python bootstrap: see [docs/REGRESSION.md](docs/REGRESSION.md).

## Demo videos (M8 / M12.2) — narration MUST stay in sync with visuals

**Unacceptable to ship or recommend:**

- Narration / TTS wording that **does not match** what appears on screen (Manim beats, VHS terminal text, timing).
- Terminal recordings showing **`command not found`**, **`No such file`**, **`error:`**, or other obvious shell failures — treat as a broken demo.
- Composed segment MP4s where **audio length and picture are clearly out of sync** because only `compose.sh` was run after a **full** narration regen (Manim/VHS were not rebuilt).

**Required workflow after changing `docs/demos/narration/*.md` or regenerating `audio/*.mp3`:**

1. Run **`cd docs/demos && ./rebuild-after-audio.sh`** (Manim + VHS + compose 01–11 + 12–14 + `full-demo-with-m12-2.mp4`).  
   Do **not** tell the user to run **`compose.sh` alone** unless you are only touching segments whose **visual source length already matches** the new audio (rare).

2. **Validate** before considering the work done:
   - **`cd docs/demos && ./validate-composed-demos.sh`** — fails if any segment MP4 is missing audio/video or A/V duration drift is too large.
   - **VHS / terminal**: re-run tapes from **`docs/demos`** (symlinks there point at repo-root `scripts/`, `tasks/`, `pipeline/`, `stacks/`); **watch** the rendered `terminal/rendered/*.mp4` (or the live run) for **“command not found”** and similar. If anything appears, fix the tape, environment, or missing symlinks — do not commit bad output.
   - **Spot-check** a few composed `recordings/*.mp4` in a real player: narration should align with on-screen content through the segment.

3. If Manim scene timing was tuned to old audio, update **`docs/demos/animations/scenes.py`** (or narration length) so beats still land correctly — then re-render Manim and re-compose.

Reference: [docs/demos/README.md](docs/demos/README.md), [docs/demos/narration/README.md](docs/demos/narration/README.md).

## Cursor / agent behavior

- **Run what you recommend.** When you tell the user to run a diagnostic or build command, **execute it in the workspace** (when the environment allows) and **read the output** before declaring success. Examples: `./validate-composed-demos.sh`, `./generate-all.sh --dry-run`, `./rebuild-after-audio.sh` or `./generate-all.sh --skip-tts`.
- **Long jobs:** log to a file so output is inspectable while the process runs, e.g.  
  `./generate-all.sh --skip-tts 2>&1 | tee /tmp/rebuild-demo.log`  
  Do **not** pipe straight into `tail -n` only — that often **buffers** and hides progress until the job exits.
- Rule **regression-iterate** (always on) reinforces regression behavior in `.cursor/rules/regression-iterate.mdc`.
