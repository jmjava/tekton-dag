# Demo video toolchain (M8 / M12.2)

All demo asset generation is driven by the **[`docgen`](../../documentation-generator/)** CLI, configured via **[`docgen.yaml`](docgen.yaml)**.

## Quick reference

| Task | Command |
|------|---------|
| Full pipeline from zero | `docgen generate-all` |
| Rebuild after new audio | `docgen rebuild-after-audio` |
| Compose specific segments | `docgen compose 01 03 05` |
| Compose M12.2 extension | `docgen compose 12 13 14` |
| Validate recordings | `docgen validate` |
| Validate (CI / pre-push) | `docgen validate --pre-push` |
| Narration lint only | `docgen lint` |
| Generate TTS audio | `docgen tts` |
| TTS dry run (preview) | `docgen tts --dry-run` |
| Single segment TTS | `docgen tts --segment 01` |
| Concatenate full demo | `docgen concat` |
| Launch wizard GUI | `docgen wizard` |

All commands auto-discover `docgen.yaml` when run from `docs/demos/`, or use `--config docgen.yaml` explicitly.

## Prerequisites

- **docgen** installed: `pip install -e /path/to/documentation-generator`
- **manim** installed: `pip install manim`
- **vhs + ttyd** in PATH (VHS terminal recording)
- **ffmpeg** installed
- **OPENAI_API_KEY** set (in repo-root `.env` or environment) — needed for TTS

## Typical workflows

**Fresh everything** (TTS + Manim + VHS + all segment MP4s + full-demo-with-m12-2):

```bash
cd docs/demos
docgen generate-all
```

**You already regenerated `audio/*.mp3`** — rebuild visuals + compose (do **not** run `compose` alone — length changes affect Manim/VHS mux too):

```bash
cd docs/demos
docgen rebuild-after-audio
```

**M12.2-only shortcut** (TTS + compose 12–14 + concat): [`./regenerate-m12-2.sh`](regenerate-m12-2.sh).

## Legacy shell scripts

The `.sh` scripts in this directory are thin wrappers around `docgen`. They still work but `docgen` is the canonical interface:

| Script | Equivalent |
|--------|-----------|
| `./generate-all.sh` | `docgen generate-all` |
| `./generate-all.sh --skip-tts` | `docgen generate-all --skip-tts` |
| `./rebuild-after-audio.sh` | `docgen rebuild-after-audio` |
| `./compose.sh` | `docgen compose` |
| `./compose.sh 12 13 14` | `docgen compose 12 13 14` |
| `./validate-composed-demos.sh` | `docgen validate --pre-push` |
| `python generate-narration.py` | `docgen tts` |

## Narration → TTS audio

Spoken audio is generated from `narration/*.md`. Conventions for TTS-friendly wording: [narration/README.md](narration/README.md).

```bash
docgen tts --segment 01   # one segment
docgen tts                 # all segments
```

**Then rebuild all videos** (not just compose — narration length affects Manim timing too):

```bash
docgen rebuild-after-audio
```

## Validate before you commit recordings

```bash
docgen validate
```

This checks every segment MP4 for: audio + video streams present, A/V drift within threshold, and narration lint (no leaked metadata, markdown syntax, or stage directions in TTS source). Use `--pre-push` for CI-friendly exit codes. A pre-push hook runs this automatically on `git push`.

## VHS tape `Output` paths

Tapes are run with **`docs/demos` as the working directory**. Use paths **relative to that directory**, e.g.:

```text
Output terminal/rendered/02-quickstart.mp4
```

Do **not** use `Output docs/demos/terminal/rendered/...` — that creates a nested `docs/demos/docs/demos/...` tree.

## Repo-root paths from `docs/demos` (VHS)

Tapes type commands like `./scripts/...` and `kubectl apply -f tasks/ -f pipeline/` as if the cwd were the **repository root**, but VHS runs with cwd **`docs/demos`**. This repo therefore keeps **symlinks** in `docs/demos/`:

| Symlink | Target |
|---------|--------|
| `scripts` | `../../scripts` |
| `tasks` | `../../tasks` |
| `pipeline` | `../../pipeline` |
| `stacks` | `../../stacks` |

**Windows:** if symlinks are missing after clone, enable **Developer Mode** and use `git clone -c core.symlinks=true …`.

## Outputs

| Kind | Location |
|------|-----------|
| TTS audio | `audio/*.mp3` |
| Manim | `animations/media/videos/scenes/720p30/*.mp4` |
| VHS | `terminal/rendered/*.mp4` |
| Final segments + concats | `recordings/*.mp4`, `full-demo.mp4` (01–11), `full-demo-with-m12-2.mp4` (01–14) |
