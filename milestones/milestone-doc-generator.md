# Milestone: doc-generator — Reusable demo generation library

> **Planned.** Extract the entire demo generation pipeline (TTS, Manim, VHS, ffmpeg composition, validation, GitHub Pages publishing) from `docs/demos/` into a standalone, pip-installable Python library at [`documentation-generator`](https://github.com/jmjava/documentation-generator). The library provides both a Python API and a `docgen` CLI. Advanced validation catches visual errors (OCR), layout issues (bounding-box analysis), audio-visual desynchronization, and narration artifacts — all before assets are committed.

## Goal

Build a **reusable Python library** (`docgen`) that any project can consume to:

1. Generate narrated demo videos from Markdown narration scripts, Manim animations, and VHS terminal tapes.
2. Compose and concatenate segments with ffmpeg.
3. **Validate** output quality automatically — OCR for visible errors, layout overlap detection, audio-visual sync, and narration linting.
4. **Publish** to GitHub Pages — generate `index.html`, deploy workflow, and LFS tracking rules from config.
5. Replace all ad-hoc shell and Python scripts currently in `tekton-dag/docs/demos/`.

Success = `pip install docgen` from the Git URL, create a `docgen.yaml`, and run `docgen generate-all` to produce validated, published demo videos.

---

## What already exists (prerequisites)

| Capability | Current location | Replaced by |
|------------|-----------------|-------------|
| TTS narration (OpenAI gpt-4o-mini-tts) | [`docs/demos/generate-narration.py`](../docs/demos/generate-narration.py) | `docgen tts` / `docgen.tts.TTSGenerator` |
| Whisper timestamp extraction | [`docs/demos/extract-timestamps.py`](../docs/demos/extract-timestamps.py) | `docgen.timestamps.TimestampExtractor` |
| ffmpeg composition (audio + video) | [`docs/demos/compose.sh`](../docs/demos/compose.sh) | `docgen compose` / `docgen.compose.Composer` |
| Master pipeline (generate-all) | [`docs/demos/generate-all.sh`](../docs/demos/generate-all.sh) | `docgen generate-all` / `docgen.pipeline.Pipeline` |
| A/V drift validation | [`docs/demos/validate-composed-demos.sh`](../docs/demos/validate-composed-demos.sh) | `docgen validate` / `docgen.validate.Validator` |
| Audio rebuild helper | [`docs/demos/rebuild-after-audio.sh`](../docs/demos/rebuild-after-audio.sh) | `docgen rebuild-after-audio` |
| M12.2 segment regeneration | [`docs/demos/regenerate-m12-2.sh`](../docs/demos/regenerate-m12-2.sh) | `docgen generate-all --segments 12,13,14` |
| GitHub Pages index | [`docs/index.html`](../docs/index.html) (hand-maintained) | `docgen pages` (auto-generated) |
| Pages deploy workflow | [`.github/workflows/pages.yml`](../.github/workflows/pages.yml) (hand-maintained) | `docgen pages` (auto-generated) |
| Manim scene definitions | [`docs/demos/animations/scenes.py`](../docs/demos/animations/scenes.py) | Stays in consuming repo; invoked by `docgen manim` |
| VHS tape files | [`docs/demos/terminal/*.tape`](../docs/demos/terminal/) | Stay in consuming repo; invoked by `docgen vhs` |
| Narration scripts | [`docs/demos/narration/*.md`](../docs/demos/narration/) | Stay in consuming repo; consumed by `docgen tts` |

---

## Target architecture

### Library repo (`documentation-generator`)

```
/home/ubuntu/github/jmjava/documentation-generator/
├── pyproject.toml              # packaging, deps, [project.scripts] docgen CLI
├── README.md
├── src/
│   └── docgen/
│       ├── __init__.py
│       ├── cli.py              # CLI dispatcher (docgen tts, compose, vhs, validate, pages, ...)
│       ├── config.py           # docgen.yaml loader, path resolution, schema validation
│       ├── tts.py              # OpenAI TTS: markdown stripping, streaming, per-segment
│       ├── timestamps.py       # Whisper timestamp extraction
│       ├── narration_lint.py   # pre-TTS text lint + post-TTS transcript lint
│       ├── vhs.py              # VHS runner + stderr error scanner
│       ├── manim_runner.py     # Manim scene invocation
│       ├── compose.py          # ffmpeg composition (Python subprocess)
│       ├── ocr.py              # OpenCV + pytesseract frame OCR for Manim/VHS MP4s
│       ├── manim_layout.py     # bounding-box overlap / spacing / edge checks
│       ├── av_sync.py          # audio-visual sync validation (Whisper + OCR)
│       ├── validate.py         # unified validator: all checks + --pre-push
│       ├── concat.py           # full-demo concatenation
│       ├── pages.py            # generate index.html, pages.yml, .gitattributes, .gitignore
│       ├── wizard.py           # narration setup wizard (Flask web GUI)
│       ├── templates/          # Jinja2 HTML templates for wizard
│       │   └── wizard.html
│       ├── static/             # CSS + JS for wizard frontend
│       │   ├── wizard.css
│       │   └── wizard.js
│       ├── pipeline.py         # orchestrate: tts → manim → vhs → compose → validate → concat → pages
│       └── config.py           # project config loader (visual map, segments, paths, env)
├── tests/
│   ├── test_config.py
│   ├── test_tts.py
│   ├── test_narration_lint.py
│   ├── test_vhs.py
│   ├── test_compose.py
│   ├── test_ocr.py
│   ├── test_manim_layout.py
│   ├── test_av_sync.py
│   ├── test_validate.py
│   ├── test_pages.py
│   ├── test_wizard.py
│   └── test_pipeline.py
└── examples/
    ├── README.md
    └── minimal-bundle/
        ├── narration/
        ├── terminal/
        └── docgen.yaml
```

### Consuming repo (`tekton-dag/docs/demos/` after migration)

```
docs/demos/
├── docgen.yaml                 # project config (segments, visual_map, TTS, validation, pages)
├── narration/*.md              # narration scripts (unchanged)
├── terminal/*.tape             # VHS tapes (unchanged)
├── animations/scenes.py        # Manim scenes (unchanged, project-specific)
├── animations/timing.json      # generated by docgen
├── audio/*.mp3                 # generated by docgen tts
├── terminal/rendered/*.mp4     # generated by docgen vhs
├── recordings/*.mp4            # generated by docgen compose + concat
└── requirements.txt            # adds: docgen @ git+https://github.com/jmjava/documentation-generator.git
```

Deleted after migration: `compose.sh`, `generate-all.sh`, `generate-narration.py`, `extract-timestamps.py`, `validate-composed-demos.sh`, `rebuild-after-audio.sh`, `regenerate-m12-2.sh`. Hand-maintained `docs/index.html` and `.github/workflows/pages.yml` replaced by auto-generated versions.

---

## Module design

### 1. `config.py` — project configuration

Loads `docgen.yaml`, resolves relative paths against the yaml location, validates required keys, and provides typed defaults. All other modules receive a `Config` object rather than reading env vars or paths directly.

Auto-discovers `docgen.yaml` by walking up from cwd.

### 2. `tts.py` — text-to-speech generation

Ports [`generate-narration.py`](../docs/demos/generate-narration.py) into a `TTSGenerator` class:

- `markdown_to_tts_plain()` strips headings, emphasis markers, links, code fences, and metadata lines
- Calls OpenAI `gpt-4o-mini-tts` with configurable voice and instructions
- Streams audio to MP3 files under `audio/`
- Supports `--segment 01` (single segment) and `--dry-run` (show stripped text without calling API)

### 3. `timestamps.py` — Whisper timestamp extraction

Ports [`extract-timestamps.py`](../docs/demos/extract-timestamps.py) into a `TimestampExtractor` class:

- Transcribes MP3 with OpenAI Whisper API
- Extracts word-level and segment-level timestamps
- Writes `animations/timing.json` for Manim scene synchronization
- Used by `av_sync.py` for validation

### 4. `narration_lint.py` — narration artifact detection

Two-stage validation to catch generation metadata that leaks into audio:

**Stage 1: pre-TTS (text lint)** — runs before calling OpenAI:

- Scans stripped narration text for leaked metadata artifacts:
  - `target duration`, `intended length`, `approximately N minutes`
  - `visual:`, `edit for voice`, stage directions in `*(...)*`
  - Markdown syntax: `# headings`, `**bold**`, `` `backticks` ``, `[links](url)`
  - Section markers: `---`, `***`, `## Script`
- **Blocks the TTS call** if matches found, reports offending lines
- Configurable deny-patterns in `docgen.yaml`

**Stage 2: post-TTS (audio transcript lint)** — runs after MP3 is generated:

- Transcribes the generated MP3 with Whisper
- Scans transcript for spoken artifact phrases:
  - "target duration", "intended length", "approximately three minutes"
  - "visual colon", "narration segment", "script section", "edit for voice"
  - "markdown", "heading", "backtick"
- Catches TTS model hallucinations and metadata the text stripper missed

### 5. `vhs.py` — VHS terminal recorder

`VHSRunner` class:

- Renders `.tape` files by invoking `vhs` subprocess
- Captures stdout and stderr
- After render, scans output for error patterns: `command not found`, `No such file`, `error:`, `Permission denied`, `syntax error`
- `--strict` mode: any unrecognized shell output producing unexpected stderr fails the build
- Returns structured results per tape (success/fail, errors found, output path)

### 6. `manim_runner.py` — Manim scene renderer

`ManimRunner` class:

- Reads scene list and quality setting from config
- Invokes `manim` subprocess on each scene in the consuming repo's `animations/scenes.py`
- Validates output MP4 exists after render
- Supports `--scene StackDAGScene` for single-scene rendering

### 7. `compose.py` — ffmpeg composition

`Composer` class rewriting [`compose.sh`](../docs/demos/compose.sh) in Python:

- `compose_simple(segment)` — single visual + audio (Manim-only or VHS-only segments)
- `compose_mixed(segment)` — concatenate multiple visual sources, then add audio (e.g., segment 03: Manim + VHS)
- `compose_still(segment)` — loop a still image to match audio duration
- `compose_image(segment)` — use a static image as the visual
- Reads `visual_map` from config to determine which method per segment
- Proper error handling with exceptions and structured logging
- All ffmpeg calls via `subprocess.run` with timeout

### 8. `ocr.py` — frame-level OCR scanning

Scans rendered MP4 frames using OpenCV + pytesseract to detect visible errors:

1. Sample frames at configurable intervals (default: every 2s, plus first/last frame)
2. Convert to grayscale, apply thresholding for clean OCR
3. Run `pytesseract.image_to_string` + `image_to_data` (bounding boxes + confidence scores)
4. Aggregate detected text across sampled frames

**VHS checks:**

- Scan for shell error patterns: `command not found`, `No such file or directory`, `bash:`, `syntax error`, `Permission denied`
- Report frame timestamp and matched text

**Manim checks:**

- Detect garbled/garbage text (low-confidence OCR regions below configurable threshold)
- Detect text too close to frame edges
- Cross-reference extracted text against expected labels (optional allowlist in config)

### 9. `manim_layout.py` — layout and spacing validation

Static analysis of rendered Manim frames for element spacing:

1. Sample key frames from Manim MP4 (first, mid, last, plus configured beat timestamps)
2. Run `pytesseract.image_to_data` to get bounding boxes of all text regions
3. **Overlap detection:** flag any pair of text regions with IoU > 0
4. **Spacing check:** flag pairs closer than `min_spacing` pixels (default: 10px)
5. **Edge clipping:** flag text within `edge_margin` pixels of frame border (default: 15px)

### 10. `av_sync.py` — audio-visual synchronization

Validates that visual content matches narration timing:

1. Transcribe audio with Whisper to get word/segment-level timestamps
2. Extract anchor keywords from transcript — important nouns, technical terms, transition phrases
3. Sample video frames at anchor timestamps from the composed MP4
4. OCR each sampled frame
5. Verify the anchor keyword (or synonym) appears in the OCR text within a configurable tolerance window (default: +/- 3s)

**What it catches:**

- Manim scene transitions that happen too early/late relative to narration
- VHS terminal segments where commands haven't appeared when the narrator describes them
- Composed videos where audio and video got swapped or badly muxed
- Scenes rebuilt with different timing after audio changed but compose wasn't re-run

Auto-extracts anchors from Whisper transcript if not configured manually.

### 11. `validate.py` — unified validator

Combines all validation checks into a single `Validator` class:

- **A/V stream presence** — both audio and video streams exist in composed MP4
- **A/V drift** — audio and video durations within configurable tolerance (default: 2.75s)
- **Narration lint (pre-TTS)** — stripped text has no leaked metadata
- **Narration lint (post-TTS)** — Whisper transcript of generated MP3 has no spoken artifacts
- **VHS stderr scan** — no shell errors in VHS build output
- **OCR content scan (VHS)** — no `command not found` or shell errors visible in pixels
- **OCR content scan (Manim)** — no garbled text or low-confidence garbage regions
- **Layout overlap (Manim)** — no overlapping text, proper edge margins, minimum spacing
- **Audio-visual sync** — narration keywords visible on screen when spoken
- `--pre-push` mode runs everything and exits non-zero on any failure (CI/pre-push hook integration)

### 12. `concat.py` — full-demo concatenation

Reads `concat` map from config and builds concatenated MP4 files using ffmpeg concat demuxer. Supports multiple concat targets (e.g., `full-demo.mp4` for segments 01-11, `full-demo-with-m12-2.mp4` for 01-14).

### 13. `pages.py` — GitHub Pages publishing

Generates and maintains all assets needed for GitHub Pages deployment:

**`docs/index.html`** — responsive video gallery:

- Reads segment config: titles, descriptions, visual type
- Probes each `recordings/*.mp4` with ffprobe for actual duration
- Generates video cards with `<video>` tags, durations, anchor IDs (`#seg-01` ... `#seg-14`)
- Generates concat demo cards from the `concat` config
- Footer with repo link and extra links from config
- Modern CSS (gradient background, grid layout, hover effects, mobile responsive)
- Idempotent: re-running updates durations and adds/removes segments to match config

**`.github/workflows/pages.yml`** — deploy workflow:

- Triggers on push to `main` when `docs/**` changes (+ `workflow_dispatch`)
- Checks out with LFS
- Cache-busts video `src` URLs with commit SHA query strings
- `actions/upload-pages-artifact` from `docs/`
- `actions/deploy-pages`

**`.gitattributes`** — LFS tracking rules:

- `docs/demos/recordings/*.mp4 filter=lfs diff=lfs merge=lfs -text`
- `docs/demos/audio/*.mp3 filter=lfs diff=lfs merge=lfs -text`
- Merges with existing `.gitattributes` if present (does not clobber)

**`docs/demos/.gitignore`** — intermediate object exclusions:

Generated from `docgen.yaml` paths so the ignore rules always match the configured directory layout:

- `.venv/` — Python virtual environment
- `animations/media/partial_movie_files/` — Manim intermediate renders
- `animations/media/videos/` — Manim output (configurable quality subdirs)
- `terminal/rendered/` — VHS rendered output
- `audio/*.mp3` — TTS output (regenerable with `OPENAI_API_KEY`)
- `slides/node_modules/`, `slides/dist/` — Slidev build artifacts
- `__pycache__/`, `*.pyc` — Python bytecode

Recordings (`recordings/*.mp4`) are intentionally **not** ignored — they are committed (tracked via LFS) so README and Pages links work. The generated `.gitignore` includes a comment explaining this.

Merges with any existing `.gitignore` entries the consuming repo already has (does not clobber custom rules).

### 14. `pipeline.py` — orchestrator

`Pipeline` class that runs the full generation workflow:

```
tts → manim → vhs → compose → validate → concat → pages
```

- Each stage is skippable via flags (`--skip-tts`, `--skip-manim`, `--skip-vhs`)
- Stages report structured results (success/fail, warnings, timings)
- Fails fast on validation errors unless `--continue-on-error` is set

### 16. `wizard.py` — production wizard (web GUI)

A local web application that serves as the full production cockpit for demo video creation. Launched via `docgen wizard` and opens in the browser. Covers the complete lifecycle: bootstrapping narration from project docs, generating assets, proofreading results, and iterating on individual segments until each is approved.

The GUI has two main views: **Setup** (initial narration bootstrapping) and **Production** (per-segment review/redo loop).

---

#### View 1: Setup — bootstrap narration from project docs

1. **Scan** — walks the consuming repo root and discovers all `.md` files (respects `.gitignore`). Builds a directory tree structure.
2. **Present** — renders:
   - A collapsible **file tree** with checkboxes to include/exclude each `.md` file as source material for narration. Directories are collapsible nodes; checking a directory checks all children. Files show a preview snippet (first ~3 lines) on hover or expand.
   - A **guidance panel** with a multi-line text input where the user provides general advice on video creation: what to emphasize, target audience, tone, technical depth, which features matter most, what to skip, etc.
   - A **segment mapping** section where the user can drag selected files into named segments (e.g., "01-architecture", "03-bootstrap-dataflow") or let the wizard auto-group by directory/topic.
   - A **generate** button that sends the selected content + guidance to the LLM to produce narration drafts.
3. **Generate** — for each segment, the wizard:
   - Concatenates the selected `.md` file contents in order
   - Sends them to an LLM (OpenAI GPT-4o or configurable) along with the user's guidance text and a system prompt that instructs the model to produce plain spoken narration (conversational prose, no markdown, written to be read aloud by TTS)
   - Writes the output to `narration/<segment>.md`
4. **Review** — the GUI shows a preview of each generated narration draft with an inline editor for manual tweaks before saving.

---

#### View 2: Production — per-segment proofread and redo

After initial narration is created (via Setup or manually), the Production view provides a segment-by-segment review workflow. The user works on **one segment at a time** and iterates until satisfied.

**Segment list panel (left sidebar):**

- All segments from `docgen.yaml` listed with status badges:
  - **Draft** — narration exists but no video yet
  - **Generated** — video composed, awaiting review
  - **Needs work** — user flagged issues during proofreading
  - **Approved** — user marked as done
- Click a segment to load it in the main review area
- Progress bar showing how many segments are approved vs total

**Main review area (per segment):**

- **Narration tab:**
  - Full text of `narration/<segment>.md` in an editable text area
  - "Regenerate narration" button — re-sends to LLM with original source docs + user guidance + optional revision notes (e.g., "make the opening shorter", "emphasize the header propagation more")
  - Revision notes text input for targeted LLM feedback
  - Diff view showing changes from previous version (if regenerated)

- **Audio tab:**
  - Play button for the generated `audio/<segment>.mp3`
  - Waveform visualization (lightweight, e.g., wavesurfer.js or simple canvas)
  - "Redo TTS" button — regenerates audio from current narration text
  - Narration lint results shown inline (pre-TTS warnings flagged before generation, post-TTS transcript issues flagged after)

- **Video tab:**
  - Embedded `<video>` player for `recordings/<segment>.mp4`
  - "Redo compose" button — recomposes video from current audio + visuals
  - Side-by-side: video player on left, validation results on right
  - Validation results panel:
    - OCR scan results (any errors detected in frames, with timestamps and screenshots)
    - Layout check results (overlap/spacing issues with frame thumbnails)
    - A/V sync check results (anchor keywords with pass/fail per timestamp)
    - A/V drift (audio vs video duration)
  - "Redo VHS" / "Redo Manim" buttons if the segment's visual source needs re-rendering

- **Actions bar (bottom):**
  - **Redo all** — re-run the full pipeline for this segment only (TTS → render → compose → validate)
  - **Mark as approved** — sets status to Approved, moves to next unapproved segment
  - **Flag for rework** — sets status to Needs Work with a note field
  - **Next / Previous** segment navigation

**Workflow:**

```
For each segment:
  1. Review narration text → edit or regenerate with revision notes
  2. Listen to audio → redo TTS if voice/pacing is off
  3. Watch composed video → check validation results
  4. If issues: redo the specific step (narration, TTS, VHS/Manim, compose)
  5. Repeat until satisfied → mark as Approved
  6. Move to next segment
```

**State persistence:** Segment statuses (Draft / Generated / Needs Work / Approved) and revision notes are stored in a `.docgen-state.json` file in the demos directory. This file survives server restarts so the user can close the wizard and resume later.

---

#### Technology

- **Backend:** Flask with API endpoints for each operation (scan, generate narration, run TTS, compose, validate, get status)
- **Frontend:** Single-page app with vanilla JS or Alpine.js/htmx. Responsive layout: sidebar segment list + tabbed main area. Video player, audio player, text editors, validation result cards.
- **LLM integration:** Uses `OPENAI_API_KEY`. Configurable model in `docgen.yaml`:

```yaml
wizard:
  llm_model: gpt-4o
  system_prompt: >-
    You are a technical writer creating narration scripts for demo videos.
    Write in plain spoken English suitable for text-to-speech. No markdown
    formatting, no headings, no bullet points. Conversational but professional
    tone, like a senior engineer presenting at a conference.
  default_guidance: ""
  exclude_patterns:
    - '**/node_modules/**'
    - '**/.pytest_cache/**'
    - '**/archive/**'
```

**What it produces:**

- `narration/*.md` — narration scripts (created or updated per segment)
- `audio/*.mp3` — TTS audio (regenerated on redo)
- `recordings/*.mp4` — composed videos (regenerated on redo)
- `.docgen-state.json` — segment review statuses and revision notes
- Optionally updates `docgen.yaml` segments list and visual_map if new segments are created

### 17. `cli.py` — command-line interface

Click or argparse dispatcher providing all subcommands:

| Command | Description |
|---------|-------------|
| `docgen tts [--segment 01] [--dry-run]` | Generate TTS audio from narration markdown |
| `docgen manim [--scene StackDAGScene]` | Render Manim animations |
| `docgen vhs [--tape 02-quickstart.tape] [--strict]` | Render VHS terminal recordings |
| `docgen compose [01 02 03]` | Compose segments (audio + video) |
| `docgen validate [--max-drift 2.75] [--pre-push]` | Run all validation checks |
| `docgen concat [--config full-demo-with-m12-2]` | Concatenate full demo files |
| `docgen pages [--force]` | Generate index.html, pages.yml, .gitattributes, .gitignore |
| `docgen wizard [--port 8501]` | Launch narration setup wizard (local web GUI) |
| `docgen generate-all [--skip-tts] [--skip-manim] [--skip-vhs]` | Run full pipeline |
| `docgen rebuild-after-audio` | Recompose + validate + concat (skip TTS/Manim/VHS) |

All commands auto-discover `docgen.yaml` by walking up from cwd.

---

## `docgen.yaml` reference

```yaml
segments:
  default: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
  all: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14']

visual_map:
  '01': { type: manim, source: StackDAGScene.mp4 }
  '02': { type: vhs, source: 02-quickstart.mp4 }
  '03': { type: mixed, sources: [HeaderPropagationScene.mp4, 03-bootstrap.mp4] }
  '04': { type: vhs, source: 04-pr-pipeline.mp4 }
  '05': { type: manim, source: InterceptRoutingScene.mp4 }
  '06': { type: manim, source: LocalDebugScene.mp4 }
  '07': { type: vhs, source: 07-orchestrator-api.mp4 }
  '08': { type: manim, source: MultiTeamScene.mp4 }
  '09': { type: vhs, source: 09-results-db.mp4 }
  '10': { type: vhs, source: 10-newman.mp4 }
  '11': { type: mixed, sources: [BlastRadiusScene.mp4, 11-graph-tests.mp4] }
  '12': { type: vhs, source: 12-regression-suite.mp4 }
  '13': { type: vhs, source: 13-management-gui-architecture.mp4 }
  '14': { type: vhs, source: 14-gui-tekton-extension.mp4 }

concat:
  full-demo.mp4: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
  full-demo-with-m12-2.mp4:
    ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14']

tts:
  model: gpt-4o-mini-tts
  voice: coral
  instructions: >-
    You are narrating a technical demo video about a CI/CD pipeline system.
    Speak in a calm, professional tone like a senior engineer giving a
    conference talk. Moderate pace. Pause briefly between sentences.
    Pronounce technical terms clearly: Tekton, Kubernetes, mirrord,
    Neo4j, Newman, Kaniko, ArgoCD, Helm.

manim:
  scenes:
    - StackDAGScene
    - HeaderPropagationScene
    - InterceptRoutingScene
    - LocalDebugScene
    - MultiTeamScene
    - BlastRadiusScene
  quality: 720p30

validation:
  max_drift_sec: 2.75
  ocr:
    sample_interval_sec: 2
    error_patterns:
      - 'command not found'
      - 'No such file'
      - 'syntax error'
      - 'Permission denied'
      - 'bash:'
    min_confidence: 40
  layout:
    min_spacing_px: 10
    edge_margin_px: 15
    check_overlap: true
  av_sync:
    enabled: true
    tolerance_sec: 3.0
    min_anchors_per_segment: 2
  narration_lint:
    pre_tts_deny_patterns:
      - 'target duration'
      - 'intended length'
      - 'visual:'
      - 'edit for voice'
      - 'approximately \d+ minutes'
    post_tts_deny_patterns:
      - 'target duration'
      - 'narration segment'
      - 'script section'
      - 'edit for voice'
    block_tts_on_pre_lint: true
    whisper_check: true

pages:
  title: "tekton-dag Demo Videos"
  subtitle: "Stack-aware CI/CD with traffic interception"
  repo_url: "https://github.com/jmjava/tekton-dag"
  docs_dir: docs
  demos_subdir: demos
  extra_links:
    - { label: "Milestone 8", href: "milestones/milestone-8.md" }
    - { label: "Milestone 12.2", href: "milestones/milestone-12.2.md" }
  segments:
    '01': { title: "Architecture overview", description: "System architecture, DAG model, polyglot support, pipelines, and extensibility features." }
    '02': { title: "Quick start", description: "Kind, Tekton, images, tasks (VHS terminal demo)." }
    '03': { title: "Bootstrap dataflow", description: "Stack bootstrap PipelineRun walkthrough." }
    '04': { title: "PR pipeline", description: "PR flow, intercepts, tests (VHS)." }
    '05': { title: "Intercept routing", description: "PR vs normal traffic routing, header-based interception." }
    '06': { title: "Local debugging", description: "mirrord integration, IDE breakpoints, live cluster debugging." }
    '07': { title: "Orchestrator API", description: "REST API, stacks, test plan, graph (VHS)." }
    '08': { title: "Multi-team Helm", description: "Helm chart deployment, team isolation, custom hooks." }
    '09': { title: "Tekton Results", description: "Results API and persisted history (VHS)." }
    '10': { title: "Newman / regression", description: "API tests and local test tiers (VHS)." }
    '11': { title: "Test-trace graph", description: "Blast radius, graph query, focused tests (mixed)." }
    '12': { title: "Regression suite (M12.2)", description: "Full regression story + agent workflows." }
    '13': { title: "Management GUI architecture (M12.2)", description: "Vue, Flask, orchestrator relationship." }
    '14': { title: "GUI Tekton extension (M12.2)", description: "Extending the GUI for Tekton." }

env_file: ../../.env
```

---

## Python API

```python
from docgen import Pipeline, Config

config = Config.from_yaml("docgen.yaml")
pipeline = Pipeline(config)
pipeline.run(skip_tts=True, skip_manim=True)  # just VHS + compose + validate + concat + pages

# Individual steps:
from docgen.tts import TTSGenerator
gen = TTSGenerator(config)
gen.generate(segment="01", dry_run=False)

from docgen.vhs import VHSRunner
runner = VHSRunner(config)
results = runner.render_all(strict=True)  # raises on "command not found"

from docgen.validate import Validator
v = Validator(config)
report = v.run_all()  # returns structured report with pass/fail per check
v.run_pre_push()      # exits non-zero on any failure

from docgen.pages import PagesGenerator
pg = PagesGenerator(config)
pg.generate_index_html()
pg.generate_pages_workflow()
pg.generate_gitattributes()
```

---

## Migration plan for tekton-dag

After the library is built:

1. Add `docgen @ git+https://github.com/jmjava/documentation-generator.git` to `docs/demos/requirements.txt`
2. Create `docs/demos/docgen.yaml` with the full config shown above
3. Delete replaced scripts: `compose.sh`, `generate-all.sh`, `generate-narration.py`, `extract-timestamps.py`, `validate-composed-demos.sh`, `rebuild-after-audio.sh`, `regenerate-m12-2.sh`
4. Delete the hand-maintained `docs/index.html` — `docgen pages` now generates it
5. Replace `.github/workflows/pages.yml` with the auto-generated version from `docgen pages`
6. Ensure `.gitattributes` has LFS rules (generated by `docgen pages`)
7. Replace hand-maintained `docs/demos/.gitignore` with auto-generated version from `docgen pages` (preserves the same intermediate-object exclusions, derived from `docgen.yaml` paths)
8. Remove redundant demo-related ignore rules from root `.gitignore` (e.g., `docs/demos/animations/media/`, `docs/demos/terminal/rendered/`) — now covered by the generated `docs/demos/.gitignore`
9. Keep unchanged: `narration/`, `terminal/`, `animations/`, `audio/`, `recordings/`, symlinks
10. Update `AGENTS.md` and `docs/demos/README.md` to reference `docgen` CLI instead of shell scripts
11. Delete `tekton-dag/documentation-generator/` (superseded by the external repo)

---

## Deliverables

### Library (`documentation-generator`)

- [ ] `pyproject.toml` — packaging with `[project.scripts]` entry point for `docgen` CLI
- [ ] `.gitignore` — library repo ignores: `.venv/`, `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, test artifacts
- [ ] `src/docgen/config.py` — yaml loader, path resolver, schema validation
- [ ] `src/docgen/tts.py` — OpenAI TTS generator with markdown stripping
- [ ] `src/docgen/timestamps.py` — Whisper timestamp extractor
- [ ] `src/docgen/narration_lint.py` — pre-TTS text lint + post-TTS transcript lint
- [ ] `src/docgen/vhs.py` — VHS runner + stderr error scanner
- [ ] `src/docgen/manim_runner.py` — Manim scene invocation
- [ ] `src/docgen/compose.py` — ffmpeg composition in Python
- [ ] `src/docgen/ocr.py` — OpenCV + pytesseract frame OCR (Manim + VHS)
- [ ] `src/docgen/manim_layout.py` — bounding-box overlap / spacing / edge checks
- [ ] `src/docgen/av_sync.py` — audio-visual synchronization validation
- [ ] `src/docgen/validate.py` — unified validator with `--pre-push`
- [ ] `src/docgen/concat.py` — full-demo concatenation
- [ ] `src/docgen/pages.py` — generate index.html, pages.yml, .gitattributes, .gitignore
- [ ] `src/docgen/pipeline.py` — full pipeline orchestrator
- [ ] `src/docgen/wizard.py` — narration setup wizard (Flask web GUI, file tree scanner, LLM narration generation)
- [ ] `src/docgen/templates/` — Jinja2 HTML templates for wizard UI (tree view, guidance panel, segment mapper, preview/edit)
- [ ] `src/docgen/static/` — CSS and JS for wizard frontend (tree checkbox controls, drag-and-drop, inline editor)
- [ ] `src/docgen/cli.py` — CLI dispatcher for all subcommands (including `wizard`)
- [ ] `tests/` — unit tests for all modules (including wizard file scanning and tree building)
- [ ] `examples/minimal-bundle/` — example docgen.yaml and content

### Migration (tekton-dag)

- [ ] `docs/demos/docgen.yaml` — project config
- [ ] `docs/demos/requirements.txt` updated with `docgen` dependency
- [ ] Old scripts deleted (7 files)
- [ ] Hand-maintained `docs/index.html` deleted (replaced by auto-generated)
- [ ] `.github/workflows/pages.yml` replaced with auto-generated version
- [ ] `.gitattributes` LFS rules generated
- [ ] `docs/demos/.gitignore` replaced with auto-generated version (intermediate objects)
- [ ] Root `.gitignore` cleaned of redundant demo-specific rules
- [ ] `AGENTS.md` and `docs/demos/README.md` updated
- [ ] `tekton-dag/documentation-generator/` stale directory deleted

---

## Success criteria

- [ ] `pip install docgen @ git+https://github.com/jmjava/documentation-generator.git` installs cleanly
- [ ] `docgen generate-all` produces all 14 segment videos + 2 concat demos from a clean state in `tekton-dag/docs/demos/`
- [ ] `docgen validate --pre-push` passes on all produced assets with zero errors
- [ ] OCR validation detects planted `command not found` in a test VHS recording
- [ ] Layout validation detects planted overlapping text in a test Manim frame
- [ ] A/V sync validation detects a deliberately mis-timed compose (wrong audio on wrong video)
- [ ] Narration lint blocks TTS when metadata leaks into stripped text
- [ ] Narration lint flags spoken artifacts in a post-TTS transcript check
- [ ] `docgen pages` generates a valid `index.html` with correct video durations from ffprobe
- [ ] `docgen pages` generates a working `.github/workflows/pages.yml`
- [ ] `docgen pages` generates a `.gitignore` that excludes intermediate objects but not committed recordings
- [ ] No intermediate objects (Manim partials, VHS rendered, audio MP3s) slip into git after migration
- [ ] All library unit tests pass
- [ ] `docgen wizard` launches a local web GUI, scans the repo, and presents `.md` files in a tree with checkboxes
- [ ] Wizard Setup view generates narration drafts from selected docs + user guidance via LLM, matching existing narration style
- [ ] Wizard Production view displays per-segment review with narration editor, audio player, video player, and validation results
- [ ] User can redo individual steps (narration, TTS, VHS/Manim, compose) for a single segment from the Production view
- [ ] Segment statuses (Draft / Generated / Needs Work / Approved) persist across wizard restarts via `.docgen-state.json`
- [ ] `tekton-dag/docs/demos/` uses only `docgen` CLI — no remaining shell scripts for generation

---

## Dependencies

### System packages

```
# ffmpeg (composition + probing)
sudo apt install ffmpeg

# VHS (terminal recording)
brew install charmbracelet/tap/vhs   # or: go install github.com/charmbracelet/vhs@latest

# Tesseract OCR (frame text extraction)
sudo apt install tesseract-ocr

# Manim system deps (cairo, pango, ffmpeg)
sudo apt install libcairo2-dev libpango1.0-dev
```

### Python packages (pyproject.toml)

```
manim
openai
opencv-python
pytesseract
pyyaml
click
flask
jinja2
```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | For TTS + Whisper | OpenAI API key |

---

## References

- [charmbracelet/vhs](https://github.com/charmbracelet/vhs) — terminal recorder
- [ManimCommunity/manim](https://github.com/ManimCommunity/manim) — animation engine
- [OpenAI TTS API](https://platform.openai.com/docs/guides/text-to-speech) — gpt-4o-mini-tts
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text) — audio transcription
- [pytesseract](https://github.com/madmaze/pytesseract) — Python OCR wrapper
- [OpenCV](https://opencv.org/) — computer vision / frame extraction
- [Milestone 8](milestone-8.md) — original demo asset milestone (partially superseded)
- [docs/demos/README.md](../docs/demos/README.md) — current demo generation docs
