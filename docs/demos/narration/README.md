# Narration scripts (TTS source)

These Markdown files are the **spoken script** for demo segments. `generate-narration.py` turns them into `audio/*.mp3` (see [demos README](../README.md)).

## Voice-first editing

TTS will read what you write literally. Prefer:

- **Spoken URLs:** `GET slash api slash stacks` instead of `` `GET /api/stacks` ``.
- **Words, not kebab-case:** “resolve stack task” instead of `resolve-stack` where it sounds robotic.
- **Pull request** in full, not “PR” or “P-R”, unless you want that pronunciation.
- **Header name:** “dev-session header” in prose; add “written x-dev-session in YAML” once if needed.
- **Numbers in speech:** “Java seventeen”, “port five thousand one”, “sixty-nine tests”.
- **Graph / Neo4j:** “Touches edges” and “Calls edges” as normal words, not `TOUCHES` / `CALLS`.
- **No grammar shortcuts:** e.g. “PipelineRun reaches Succeeded”, not “pipeline to succeeded”.

Files with `## Script` (segments 12–14): only that section is sent to TTS; headings above it are notes for humans.

After edits, regenerate audio with `generate-narration.py`, then rebuild **all** visuals and composed MP4s:

`cd docs/demos && ./rebuild-after-audio.sh` (not `compose.sh` alone — length changes affect Manim/VHS mux too).
