# Video framework (portable)

Combines **TTS narration** (OpenAI), **optional Manim**, **VHS terminal recordings**, and **ffmpeg** to produce **per-segment MP4s** and optional **full concat**.

Derived from **tekton-dag** `docs/demos/`. Paths assume these files live together in a single directory (e.g. `your-repo/docs/demos/`).

## Prerequisites

| Tool | Role |
|------|------|
| **Python 3.10+** | `generate-narration.py`, optional Manim |
| **ffmpeg** | compose + concat |
| **VHS** | `go install github.com/charmbracelet/vhs@latest` (often `~/go/bin/vhs`) |
| **ttyd** | Required by VHS (e.g. `~/.local/bin/ttyd`); extend `PATH` in `generate-all.sh` if needed |
| **Manim** | Optional; only if you use `manim:` segments in `compose.sh` |
| **OPENAI_API_KEY** | For TTS (`generate-narration.py`); or `--skip-tts` |

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Layout (in your project)

```text
docs/demos/                    # or any single “bundle” directory
  compose.sh
  generate-all.sh
  generate-narration.py
  requirements.txt
  narration/                   # NN-topic.md → audio/NN-topic.mp3
  audio/                       # generated MP3s
  terminal/*.tape                # VHS sources
  terminal/rendered/*.mp4      # VHS outputs (gitignore or LFS)
  animations/                  # optional Manim (scenes.py + media/)
  recordings/                  # composed segment MP4s + full-demo.mp4
```

## Customize `compose.sh`

1. Set **`DEFAULT_SEGMENTS`** (e.g. `01 02 03`) — used when you run `./compose.sh` with no args.
2. Set **`FULL_CONCAT_SEGMENTS`** — ordered list to concat into `recordings/full-demo.mp4` when every listed segment composed successfully (empty `()` disables).
3. Fill **`VISUAL_MAP`** — per segment:
   - `manim:SceneFile.mp4` — under `animations/media/videos/scenes/720p30/` (or `480p15`)
   - `vhs:file.mp4` — under `terminal/rendered/`
   - `mixed:manim.mp4:vhs.mp4` — concat two videos then mux audio
   - `still:RRGGBB` — solid color 1280×720
   - `image:../path/from/demos-dir/to.png` — still PNG, scaled/padded to 1280×720 for full audio duration (add `compose_image` + `image)` case — see tekton-dag `docs/demos/compose.sh`)

Narration files must be named `NN-*.md` (e.g. `01-intro.md`); audio must be `audio/<same-stem>.mp3`.

## Customize `generate-narration.py`

- Edit **`INSTRUCTIONS`** for your product name and glossary.
- **`load_env()`** checks `DEMOS_DIR/../../.env` then `DEMOS_DIR/../.env` for `OPENAI_API_KEY`.

## Customize `generate-all.sh`

- **`MANIM_SCENES`**: empty to skip Manim; or `Scene1 Scene2` matching `animations/scenes.py`.
- **`ENV_FILE`**: where to `source` secrets (default `../../.env` from `docs/demos`).
- Title strings: search for “Demo Asset Generator”.

## VHS tapes

Run from the **demos directory** (same as `compose.sh`). In each `.tape`:

```text
Output terminal/rendered/my-segment.mp4
Set FontSize 14
...
```

## Git LFS (optional)

Large MP4s: see `.gitattributes.example`.

## Upstream

Refresh this folder from tekton-dag when the canonical scripts change:

```bash
cp docs/demos/compose.sh documentation-generator/video-framework/
cp docs/demos/generate-narration.py documentation-generator/video-framework/
# merge any project-specific edits (DEFAULT_SEGMENTS, FULL_CONCAT_SEGMENTS, etc.)
```
