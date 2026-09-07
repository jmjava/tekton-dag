# Maintainer hints for tekton-dag demos

Committed **inputs** for OpenAI-backed `docgen` commands. Paths in front matter are
**repo-root-relative** (see `repo_root:` in `docgen.yaml`).

This bundle targets **current docgen** (Manim + TTS + ffmpeg). There is **no VHS /
terminal-tape** stage — former tape segments are rewired as Manim scenes via
`wiring.visual` in each `segment-*.md`.

## Workflow

1. Edit `hints/*.md` (YAML front matter + editorial body).
2. Run from `docs/demos/`:

```bash
docgen --config docgen.yaml yaml-generate
```

3. Review the `docgen.yaml` diff (tool-produced). Do **not** hand-edit merged
   `visual_map` / `narration_from_source` / `manim_scene_generation` / `concat`
   blocks when this hints tree is the source of truth.

4. Full content regen (after yaml-generate), current docgen:

```bash
docgen --config docgen.yaml narration-generate --all --force
docgen --config docgen.yaml scene-spec-generate --all
docgen --config docgen.yaml generate-all
# generate-all: TTS -> local timestamps -> image-generate (missing) -> Manim -> compose -> validate -> concat -> pages
```

## Front matter

- **`docgen.segment`**: `{ create: true, id, stem }` → `segments.*` + `segment_names`
- **`docgen.wiring.visual`**: full `visual_map` entry (`type: manim` + `scene` + `source`)
- **`docgen.wiring.narration`**: per-segment narration_from_source hints + context
- **`docgen.wiring.manim_scene`**: steers `scene-spec-generate`
- **`docgen.project`** (in `project-context.md`): global narration hints, `env_file`,
  `discovery.auto_visual_map: false`, and `concat` lists (including segment **19**)

## Accuracy north star (Jul 2026)

- Four pipelines: bootstrap, PR, merge, **promote**
- M13 foundations shipped; remaining M13 items are open (not “the whole milestone is future”)
- M14 operator (CRD-primary); Helm `operator.enabled` default **on**
- Segment **19** deep-dives the operator; segment **18** is post-M14 / remaining open items only
