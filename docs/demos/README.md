# Demo video toolchain (M8 / M12.2)

Regenerate narration, animations, terminal recordings, and composed MP4s:

```bash
cd docs/demos
./generate-all.sh
```

**Prerequisites:** see header comments in [`generate-all.sh`](generate-all.sh) (Python venv + Manim, **VHS + ttyd**, ffmpeg, `OPENAI_API_KEY` for TTS).

Terminology for **which cluster is “production”** vs **validation / baseline** is documented in [`../ENVIRONMENTS-AND-CLUSTERS.md`](../ENVIRONMENTS-AND-CLUSTERS.md); narration in `narration/*.md` follows that model.

## Narration → TTS audio

Spoken audio is generated from `narration/*.md` by [`generate-narration.py`](generate-narration.py). **Editing those Markdown files does not change existing MP3s** until you re-run TTS, for example:

```bash
cd docs/demos && source .venv/bin/activate
python generate-narration.py --segment 01   # one segment prefix
python generate-narration.py                # all segments
```

Then re-run [`compose.sh`](compose.sh) for the affected segments so `recordings/*.mp4` match the new audio.

## VHS tape `Output` paths

Tapes are run with **`docs/demos` as the working directory**. Use paths **relative to that directory**, e.g.:

```text
Output terminal/rendered/02-quickstart.mp4
```

Do **not** use `Output docs/demos/terminal/rendered/...` — that creates a nested `docs/demos/docs/demos/...` tree and `compose.sh` will not find the files.

## Outputs

| Kind | Location |
|------|-----------|
| TTS audio | `audio/*.mp3` |
| Manim | `animations/media/videos/scenes/720p30/*.mp4` |
| VHS | `terminal/rendered/*.mp4` |
| Final segments + concats | `recordings/*.mp4`, `full-demo.mp4` (01–11), `full-demo-with-m12-2.mp4` (01–14) |

**Static illustrations** (split PNG panels for docs/thumbnails): see [`../assets/README.md`](../assets/README.md) and `../assets/panels/*.png` (regenerate with `docs/assets/split_composites.py` using this folder’s `.venv`).
