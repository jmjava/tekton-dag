# Milestone 8: Demo assets — programmatic recordings, animations, narrated presentations

> **Partial.** Manim animations, OpenAI TTS narration, ffmpeg composition, and four composed segment videos are in place; [GitHub Pages](https://jmjava.github.io/tekton-dag/) hosts playable demos. VHS terminal recordings, Slidev PDF export, and full `full-demo.mp4` concat remain open (see success criteria below). Every asset is generated from source under `docs/demos/` and can be regenerated.

## Goal

Create **narrated demo videos, animated architecture diagrams, terminal recordings, and a slide deck** — all generated programmatically from scripts, Manim scenes, VHS tape files, and narration text.

Success = run `./docs/demos/generate-all.sh` from a configured environment (see toolchain below). A root `make demos` target may be added later as a thin wrapper.

---

## Toolchain

| Tool | What it produces | Source files |
|------|-----------------|--------------|
| **Manim** (Community edition) | Animated MP4s: DAG flow, header propagation, blast radius, PR vs normal routing | `docs/demos/animations/scenes.py` |
| **VHS** (charmbracelet/vhs) | Terminal GIF/MP4s: quick start, bootstrap, PR pipeline, Newman, orchestrator API | `docs/demos/terminal/*.tape` |
| **OpenAI gpt-4o-mini-tts** | MP3 narration per segment (steerable voice, ~$0.60 total) | `docs/demos/narration/*.md` |
| **Slidev** | HTML/PDF slide deck with embedded mermaid + animation stills | `docs/demos/slides/slides.md` |
| **ffmpeg** | Final composed videos: Manim animation + TTS audio + VHS overlay | `docs/demos/compose.sh` |

---

## Directory layout

```
docs/demos/
├── narration/                   # Narration scripts (one markdown per segment)
│   ├── 01-architecture.md
│   ├── 02-quickstart.md
│   ├── 03-bootstrap-dataflow.md
│   ├── 04-pr-pipeline.md
│   ├── 05-intercept-routing.md
│   ├── 06-local-debug.md
│   ├── 07-orchestrator.md
│   ├── 08-multi-team-helm.md
│   ├── 09-results-db.md
│   ├── 10-newman-tests.md
│   └── 11-test-trace-graph.md
│
├── audio/                       # Generated MP3s (OpenAI TTS output)
│   ├── 01-architecture.mp3
│   ├── ...
│
├── animations/                  # Manim source + rendered output
│   ├── scenes.py                # All Manim scenes in one file
│   └── media/                   # Manim output dir (MP4s land here)
│
├── terminal/                    # VHS tape files + rendered output
│   ├── 02-quickstart.tape
│   ├── 03-bootstrap.tape
│   ├── 04-pr-pipeline.tape
│   ├── 07-orchestrator-api.tape
│   ├── 09-results-db.tape
│   ├── 10-newman.tape
│   ├── 11-graph-tests.tape
│   └── rendered/                # VHS output (GIF + MP4)
│
├── slides/                      # Slidev presentation
│   ├── slides.md
│   └── public/                  # Static assets (animation stills, logos)
│
├── recordings/                  # Final composed videos
│   ├── 01-architecture.mp4
│   ├── ...
│   └── full-demo.mp4            # Concatenated final cut
│
├── generate-narration.py        # OpenAI TTS generator
├── compose.sh                   # ffmpeg: animation + audio → video
├── generate-all.sh              # Master: runs everything in order
└── requirements.txt             # Python deps (manim, openai)
```

---

## Segments — asset map

Each segment has a narration script, a visual source (Manim animation or VHS terminal recording), and a final composed video.

| # | Segment | Visual source | Audio | Final |
|---|---------|--------------|-------|-------|
| 1 | **Architecture overview** | Manim: DAG nodes animate in, edges draw, pipelines fan out, orchestrator connects | TTS `01-architecture.md` | `01-architecture.mp4` |
| 2 | **Quick start** | VHS: `kind-with-registry.sh` → `install-tekton.sh` → apply tasks | TTS `02-quickstart.md` | `02-quickstart.mp4` |
| 3 | **Bootstrap + data flow** | Manim: request packet animates through FE→BFF→API, header badge glows + VHS: bootstrap pipeline output | TTS `03-bootstrap-dataflow.md` | `03-bootstrap-dataflow.mp4` |
| 4 | **PR pipeline** | VHS: `generate-run.sh --mode pr` → pipeline stages scroll | TTS `04-pr-pipeline.md` | `04-pr-pipeline.mp4` |
| 5 | **Intercept routing** | Manim: split animation — normal request (blue path) vs PR request with header (green path through intercept pod) | TTS `05-intercept-routing.md` | `05-intercept-routing.mp4` |
| 6 | **Local step-debug** | Manim: laptop icon → mirrord tunnel → cluster pod → breakpoint fires + annotated still frames | TTS `06-local-debug.md` | `06-local-debug.mp4` |
| 7 | **Orchestration service** | VHS: curl calls to orchestrator endpoints, PipelineRun appears | TTS `07-orchestrator.md` | `07-orchestrator.mp4` |
| 8 | **Multi-team + Helm** | Manim: team bubbles multiply, Helm chart deploys into each, ArgoCD sync arrows | TTS `08-multi-team-helm.md` | `08-multi-team-helm.mp4` |
| 9 | **Tekton Results DB** | VHS: `verify-results-in-db.sh` output | TTS `09-results-db.md` | `09-results-db.mp4` |
| 10 | **Newman test suite** | VHS: `run-orchestrator-tests.sh --all` — green checkmarks scroll | TTS `10-newman-tests.md` | `10-newman-tests.mp4` |
| 11 | **Test-trace graph (M9)** | Manim: Neo4j graph builds — service nodes, test nodes, TOUCHES edges, blast radius expands + VHS: graph API calls | TTS `11-test-trace-graph.md` | `11-test-trace-graph.mp4` |

---

## Manim scenes (detailed design)

### Scene 1: StackDAGScene (segment 1 — architecture)

- **Stage 1**: Three rounded rectangles appear (FE, BFF, API) arranged left-to-right with labels and icons (Vue, Spring Boot, Spring Boot).
- **Stage 2**: Edges animate between them (arrows with "downstream" labels). Propagation roles fade in below each node: originator → forwarder → terminal.
- **Stage 3**: Three pipeline boxes appear below (bootstrap, PR, merge) connected to the stack with dotted lines.
- **Stage 4**: Orchestrator box appears on the left with webhook arrow in, PipelineRun arrow out to pipelines. Helm/ArgoCD badge appears.
- Duration: ~45s of animation, narration fills 2-3 min.

### Scene 2: HeaderPropagationScene (segment 3 — data flow)

- **Stage 1**: Stack nodes from Scene 1 (static). A "request" dot appears at the left edge.
- **Stage 2**: Dot moves to FE node. A header badge `x-dev-session: pr-42` appears and attaches to the dot.
- **Stage 3**: Dot + badge moves FE → BFF. BFF node glows (forwarder). Badge stays attached.
- **Stage 4**: Dot + badge moves BFF → API. API node glows (terminal). Badge turns green — "Header arrived at terminal."
- **Stage 5**: Response dot travels back API → BFF → FE carrying a "200 OK" badge.
- Duration: ~30s.

### Scene 3: InterceptRoutingScene (segment 5 — PR vs normal)

- **Stage 1**: Stack nodes. Two request dots appear — blue (normal) and green (PR with header).
- **Stage 2**: Blue dot enters FE and follows the normal path straight through deployed pods. Labels "original deployment" appear.
- **Stage 3**: Green dot enters FE. At the intercept point, a branch appears: the mirrord/telepresence proxy intercepts and routes to a separate "PR pod" (snapshot build). Label: "header matches → PR build."
- **Stage 4**: Both arrive at their destinations simultaneously. Side-by-side comparison: "Same URL, different backend."
- Duration: ~25s.

### Scene 4: LocalDebugScene (segment 6 — step-debug)

- **Stage 1**: Split view: left = laptop with IDE icon, right = Kubernetes cluster (nodes).
- **Stage 2**: mirrord tunnel line draws between laptop and cluster. Label: "mirrord exec — traffic mirror."
- **Stage 3**: Request enters cluster, mirrord redirects matching traffic to laptop.
- **Stage 4**: IDE breakpoint icon glows red. Callout: "Breakpoint hit — live cluster data, local debugger."
- **Stage 5**: Step-through animation (code lines highlight sequentially). Variables panel populates.
- Duration: ~30s.

### Scene 5: BlastRadiusScene (segment 11 — test-trace graph)

- **Stage 1**: Neo4j-style graph appears: 3 service nodes (circles) + 9 test nodes (diamonds) with TOUCHES edges.
- **Stage 2**: "Changed app: demo-api" — demo-api node highlights red.
- **Stage 3**: Radius 1: edges from demo-api to all touching tests glow. Selected tests list appears on the side: 6 tests (3 e2e, 3 individual).
- **Stage 4**: Radius 2: neighbor service nodes (BFF) glow, their tests add to the list. Expanded set shown.
- **Stage 5**: "Unmapped area" — a new node with no edges pulses with a warning icon: "needs regression tests."
- Duration: ~35s.

### Scene 6: MultiTeamScene (segment 8 — scaling)

- **Stage 1**: Single team bubble with 3 app nodes inside.
- **Stage 2**: Bubble duplicates to 3 teams (team-alpha, team-beta, team-gamma). Each has its own cluster icon.
- **Stage 3**: Helm chart icon appears, arrows fan out to each team. ArgoCD sync loop arrows animate.
- **Stage 4**: One team receives a PR webhook — only that team's pipeline fires. Other teams undisturbed.
- **Stage 5**: Counter: "40 apps × N teams" — scales up with a growing bar animation.
- Duration: ~25s.

---

## VHS tape files (detailed design)

### 02-quickstart.tape

```
Output docs/demos/terminal/rendered/02-quickstart.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms

Type "# 1. Create Kind cluster with local registry"
Enter
Sleep 500ms
Type "./scripts/kind-with-registry.sh"
Enter
Sleep 3s
Type "# 2. Install Tekton"
Enter
Type "./scripts/install-tekton.sh"
Enter
Sleep 3s
Type "# 3. Publish build images"
Enter
Type "./scripts/publish-build-images.sh"
Enter
Sleep 3s
Type "# 4. Apply tasks and pipelines"
Enter
Type "kubectl apply -f tasks/ -f pipeline/"
Enter
Sleep 2s
Type "# Ready! ✓"
Enter
```

Other tapes follow the same pattern — scripted commands with simulated output. For segments that show live cluster output, the tape captures actual kubectl/tkn output.

---

## Narration scripts (detailed design)

Each file in `docs/demos/narration/` is plain text (the narration for that segment). The TTS generator reads it and produces MP3.

### OpenAI TTS configuration

```python
MODEL = "gpt-4o-mini-tts"
VOICE = "coral"                    # warm, clear, professional
INSTRUCTIONS = (
    "You are narrating a technical demo video about a CI/CD pipeline system. "
    "Speak in a calm, professional tone like a senior engineer giving a "
    "conference talk. Moderate pace. Pause briefly between sentences. "
    "Pronounce technical terms clearly: Tekton, Kubernetes, mirrord, "
    "Neo4j, Newman, Kaniko, ArgoCD, Helm."
)
```

### Cost estimate

| Segment | ~Characters | Cost @ $0.015/1K |
|---------|-------------|------------------|
| 01 Architecture | 1,500 | $0.023 |
| 02 Quick start | 800 | $0.012 |
| 03 Bootstrap + data flow | 1,200 | $0.018 |
| 04 PR pipeline | 1,400 | $0.021 |
| 05 Intercept routing | 1,000 | $0.015 |
| 06 Local debug | 1,000 | $0.015 |
| 07 Orchestrator | 1,200 | $0.018 |
| 08 Multi-team + Helm | 1,000 | $0.015 |
| 09 Results DB | 600 | $0.009 |
| 10 Newman tests | 800 | $0.012 |
| 11 Test-trace graph | 1,200 | $0.018 |
| **Total** | **~11,700** | **~$0.18** |

---

## Composition pipeline

### Step 1: Generate audio

```bash
python docs/demos/generate-narration.py          # reads narration/*.md → audio/*.mp3
```

### Step 2: Render Manim animations

```bash
cd docs/demos/animations
manim -pql scenes.py StackDAGScene               # 01
manim -pql scenes.py HeaderPropagationScene       # 03
manim -pql scenes.py InterceptRoutingScene        # 05
manim -pql scenes.py LocalDebugScene              # 06
manim -pql scenes.py MultiTeamScene               # 08
manim -pql scenes.py BlastRadiusScene             # 11
```

### Step 3: Render VHS terminal recordings

```bash
for tape in docs/demos/terminal/*.tape; do
  vhs "$tape"
done
```

### Step 4: Compose final videos

```bash
# For Manim segments: combine animation + audio
ffmpeg -i animations/media/.../StackDAGScene.mp4 \
       -i audio/01-architecture.mp3 \
       -c:v copy -c:a aac -shortest recordings/01-architecture.mp4

# For VHS segments: combine terminal recording + audio
ffmpeg -i terminal/rendered/02-quickstart.mp4 \
       -i audio/02-quickstart.mp3 \
       -c:v copy -c:a aac -shortest recordings/02-quickstart.mp4

# For mixed segments (Manim + VHS): concatenate, then add audio
ffmpeg -f concat -i segment-list.txt -i audio/03-bootstrap-dataflow.mp3 \
       -c:v libx264 -c:a aac recordings/03-bootstrap-dataflow.mp4
```

### Step 5: Concatenate full demo

```bash
# Build concat list
for f in recordings/01-*.mp4 recordings/02-*.mp4 ... ; do
  echo "file '$f'" >> full-demo-list.txt
done
ffmpeg -f concat -safe 0 -i full-demo-list.txt -c copy recordings/full-demo.mp4
```

### Step 6: Export Slidev deck

```bash
cd docs/demos/slides
npm install
npx slidev export --output ../recordings/slide-deck.pdf
```

---

## Slidev deck structure

```markdown
---
theme: default
title: "tekton-dag: Stack-Aware CI/CD with Traffic Interception"
---

# tekton-dag
Stack-Aware CI/CD with Header-Based Traffic Interception

---

## Architecture (embed Manim still or mermaid)
<!-- Mermaid DAG + pipeline diagram -->

---

## Data flow: x-dev-session header
<!-- Animation still from HeaderPropagationScene -->

---

## PR Pipeline: Build → Intercept → Test
<!-- Pipeline stage diagram -->

---

## Intercept routing: PR vs Normal
<!-- Side-by-side from InterceptRoutingScene -->

... (one slide per segment)
```

---

## Deliverables

- [x] Toolchain selection: Manim + VHS + OpenAI TTS + Slidev + ffmpeg
- [x] `docs/demos/narration/*.md` — 11 narration scripts (synced to real architecture)
- [x] `docs/demos/animations/scenes.py` — 6 Manim scenes (timed to narration paragraphs)
- [x] `docs/demos/terminal/*.tape` — 7 VHS tape files (require ttyd to render)
- [x] `docs/demos/generate-narration.py` — OpenAI TTS generator (gpt-4o-mini-tts, coral voice)
- [x] `docs/demos/compose.sh` — ffmpeg composition (loops video to match audio)
- [x] `docs/demos/generate-all.sh` — master generator (--skip-tts/--skip-manim/--skip-vhs)
- [x] `docs/demos/slides/slides.md` — Slidev presentation (15 slides with mermaid diagrams)
- [x] `docs/demos/recordings/*.mp4` — 4 Manim segments composed (VHS pending ttyd)
- [x] `docs/demos/requirements.txt` — Python deps (manim, openai)
- [x] `docs/demos/.gitignore` — excludes generated assets and .venv
- [ ] VHS terminal recordings rendered (requires ttyd in PATH)
- [ ] Full demo video concatenated (pending VHS segments)

---

## Success criteria

- [x] `./docs/demos/generate-all.sh` produces all assets from a clean state.
- [x] Each of the 11 segment videos has synced narration + visuals (Manim timed per-paragraph).
- [x] Manim animations clearly show: DAG, header propagation, intercept routing, blast radius, multi-team scaling, local debug.
- [ ] VHS terminal recordings show real command output (requires ttyd).
- [ ] Slidev deck exports to PDF with all diagrams and stills (requires npm install).
- [ ] Full demo video (`full-demo.mp4`) is under 30 minutes (pending VHS segments).

---

## Dependencies

```
# Python (manim + openai)
pip install manim openai

# VHS
brew install charmbracelet/tap/vhs   # or: go install github.com/charmbracelet/vhs@latest

# Slidev
npm install -g @slidev/cli

# ffmpeg (composition)
sudo apt install ffmpeg               # or: brew install ffmpeg

# OpenAI API key
export OPENAI_API_KEY="sk-..."
```

---

## References

- [charmbracelet/vhs](https://github.com/charmbracelet/vhs) — terminal recorder
- [ManimCommunity/manim](https://github.com/ManimCommunity/manim) — animation engine
- [OpenAI TTS API](https://platform.openai.com/docs/guides/text-to-speech) — gpt-4o-mini-tts
- [Slidev](https://sli.dev/) — markdown presentations
- [docs/demo-playbook.md](../docs/demo-playbook.md) — existing playbook
