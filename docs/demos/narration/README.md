# Narration scripts (TTS source)

These Markdown files are the **spoken script** for demo segments. `docgen tts` turns them into `audio/*.mp3` (see [demos README](../README.md)).

## Voice-first editing

TTS will read what you write literally. Prefer:

- **Spoken URLs:** `GET slash api slash stacks` instead of `` `GET /api/stacks` ``.
- **Words, not kebab-case:** "resolve stack task" instead of `resolve-stack` where it sounds robotic.
- **Pull request** in full, not "PR" or "P-R", unless you want that pronunciation.
- **Header name:** "dev-session header" in prose; add "written x-dev-session in YAML" once if needed.
- **Numbers in speech:** "Java seventeen", "port five thousand one", "sixty-nine tests".
- **Graph / Neo4j:** "Touches edges" and "Calls edges" as normal words, not `TOUCHES` / `CALLS`.
- **No grammar shortcuts:** e.g. "PipelineRun reaches Succeeded", not "pipeline to succeeded".

## Lint before TTS

Run `docgen lint` to check all narration files for leaked metadata, markdown syntax, or stage directions that should not be sent to TTS. This check also runs automatically as part of `docgen validate`.

## After edits

Regenerate audio and rebuild all visuals + composed MP4s:

```bash
docgen tts                     # regenerate audio
docgen rebuild-after-audio     # Manim + VHS + compose + validate + concat
```

Do not run `docgen compose` alone after changing narration — length changes affect Manim/VHS mux timing too.
