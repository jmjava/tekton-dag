# Manim declarative scene specs (tekton-dag)

Use these constraints when generating **`animations/specs/*.scene.yaml`**
(via `docgen scene-spec-generate`):

- **Rows of `_box` only** — short ASCII labels; use `->` or hyphen, not unicode arrows.
- **Pages, not shrinking:** use top-level **`pages`** when the story needs more boxes
  than fit on one screen. Prefer extra pages or shorter boxes over tall stacks.
- **Subject-beat coverage (mandatory):** hold the board while sentences elaborate the
  same topic; when the topic shifts, add a spoken-phrase label for that beat. Docgen
  checks **beat coverage** and rejects invented unspoken labels — not a blind count.
- **~3 rows per page** is a safe default; match beats in narration and optional
  `wait_segment` / `wait_at` when `timing.json` has Whisper data.
- **Palette tokens only:** `C_BG`, `C_ACCENT`, `C_GREEN`, `C_ORANGE`, `C_BLUE`,
  `C_RED`, `C_TEAL`, `C_PURPLE`, `C_WHITE`.
- **Readable sizes:** `font_size` ≥ 14; widths ~3–6, heights ~0.7–1.3.
- Layout gate: `scene-spec-generate` rejects specs that exceed vertical stack budget
  or safe row width. Fix via pages / shorter rows, not by hand-editing generated
  `scenes.py` marker blocks.
- **Optional image elements:** `{ image: images/<name>.png, width, height, prompt, label }`
  — `docgen image-generate` (also inside `generate-all`) fills missing PNGs from the
  prompt via OpenAI Images. Prefer diagrams as `_box` rows; use images only when a
  photo/illustration beat is clearer than boxes.
- **Timing (tekton-dag):** always `docgen timestamps --engine whisper` (pinned via
  `timestamps.engine: whisper` in project-context). Do **not** use the local
  silencedetect engine for shippable demos.
- **Spoken anchors only:** every box `label` must be a short phrase that appears in
  that segment’s narration (same wording the TTS speaks). Never invent diagram-only
  vocabulary (e.g. Originator / Demo-fe) unless those exact words are spoken.
- **Regen order:** narration → TTS → **Whisper timestamps** → scene-spec-generate /
  scene-compile → Manim → compose. Re-compile after timestamps so `wait_word` matches.
