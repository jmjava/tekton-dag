# Demo video toolchain (M8 / M12.2)

**Portable copy** for other repos: [`../../documentation-generator/video-framework/`](../../documentation-generator/video-framework/) (+ [`../../documentation-generator/example-demo-bundle/`](../../documentation-generator/example-demo-bundle/)). Canonical scripts stay here; refresh the copy when the framework changes.

**Full pipeline from zero** (TTS + Manim + VHS + all segment MP4s + `full-demo-with-m12-2.mp4`):

```bash
cd docs/demos
./generate-all.sh
```

**You already regenerated `audio/*.mp3`** with `generate-narration.py` — run **everything else** (do **not** stop at `compose.sh` alone):

```bash
cd docs/demos
./rebuild-after-audio.sh
```

That is the same as `./generate-all.sh --skip-tts` (Manim, VHS, compose 01–11, compose 12–14, concat full demo).

**M12.2-only shortcut** (TTS + compose 12–14 + concat, assumes core 01–11 already OK): [`./regenerate-m12-2.sh`](regenerate-m12-2.sh).

**Prerequisites:** see header comments in [`generate-all.sh`](generate-all.sh) (Python venv + Manim, **VHS + ttyd**, ffmpeg, `OPENAI_API_KEY` for TTS).

Terminology for **which cluster is “production”** vs **validation / baseline** is documented in [`../ENVIRONMENTS-AND-CLUSTERS.md`](../ENVIRONMENTS-AND-CLUSTERS.md); narration in `narration/*.md` follows that model.

## Narration → TTS audio

Spoken audio is generated from `narration/*.md` by [`generate-narration.py`](generate-narration.py). Conventions for TTS-friendly wording: [narration/README.md](narration/README.md). The script **strips Markdown** (headings, bold, backticks, links) and, if the file has a `## Script` section (M12.2 segments 12–14), sends **only that section** to TTS — not the title line or “Target duration / Visual” notes. **Editing those Markdown files does not change existing MP3s** until you re-run TTS, for example:

```bash
cd docs/demos && source .venv/bin/activate
python generate-narration.py --segment 01   # one segment prefix
python generate-narration.py                # all segments
```

**Then rebuild all videos** (not just `compose.sh` — narration length affects Manim timing too):

```bash
./rebuild-after-audio.sh
```

## Validate before you commit recordings

```bash
cd docs/demos
./validate-composed-demos.sh
```

Fails if a segment MP4 is missing an audio or video stream, or if stream durations drift more than a few seconds (sign of a partial rebuild). **Also** watch VHS output for **`command not found`** / errors — that is never acceptable in published terminal demos. See **[AGENTS.md](../../AGENTS.md)** (demo section).

## VHS tape `Output` paths

Tapes are run with **`docs/demos` as the working directory**. Use paths **relative to that directory**, e.g.:

```text
Output terminal/rendered/02-quickstart.mp4
```

Do **not** use `Output docs/demos/terminal/rendered/...` — that creates a nested `docs/demos/docs/demos/...` tree and `compose.sh` will not find the files.

## Repo-root paths from `docs/demos` (VHS)

Tapes type commands like `./scripts/...` and `kubectl apply -f tasks/ -f pipeline/` as if the cwd were the **repository root**, but VHS runs with cwd **`docs/demos`**. This repo therefore keeps **symlinks** in `docs/demos/`:

| Symlink | Target |
|---------|--------|
| `scripts` | `../../scripts` |
| `tasks` | `../../tasks` |
| `pipeline` | `../../pipeline` |
| `stacks` | `../../stacks` |

So the shell resolves those paths correctly while recording. `scripts/common.sh` sets **`REPO_ROOT` from the physical `scripts/` directory** (`cd -P`), so scripts still find `tests/`, `libs/`, etc., when invoked via the symlink.

**Windows:** if symlinks are missing after clone, enable **Developer Mode** (or clone as admin) and use `git clone -c core.symlinks=true …` so Git creates real symlinks.

## Outputs

| Kind | Location |
|------|-----------|
| TTS audio | `audio/*.mp3` |
| Manim | `animations/media/videos/scenes/720p30/*.mp4` |
| VHS | `terminal/rendered/*.mp4` |
| Final segments + concats | `recordings/*.mp4`, `full-demo.mp4` (01–11), `full-demo-with-m12-2.mp4` (01–14) |

**Static illustrations** (split PNG panels for docs/thumbnails): see [`../assets/README.md`](../assets/README.md) and `../assets/panels/*.png` (regenerate with `docs/assets/split_composites.py` using this folder’s `.venv`).
