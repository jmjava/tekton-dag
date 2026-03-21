# Static assets (illustrations & logo)

## Composite sources (full sheets)

These are the original multi-panel PNGs in this folder (often from AI / batch export):

| File | Layout |
|------|--------|
| `a_collection_of_four_digital_illustrations_related.png` | 2×2 (1536×1024) |
| `a_set_of_four_digital_illustrations_related_to_te.png` | 2×2 (1536×1024) |
| `a_set_of_nine_informational_and_illustrative_graph.png` | 3×3 (1536×1024) |
| `a_logo_for_tekton_dag_is_displayed_in_a_2d_digit.png` | Single square (1024×1024) |

## Panel index (machine-readable)

**[`panels-index.json`](panels-index.json)** maps each file in `panels/` to:

- **content** — title, short summary, keywords  
- **suggestedPlacement** — example docs (paths relative to `docs/`) and why the image fits  

Use it to decide where to embed images in Markdown or on GitHub Pages. Update the JSON when you add panels or rename docs.

## Individual panels (for READMEs & demos)

Split outputs live under **`panels/`**. Regenerate them after replacing a composite:

```bash
# From repo root (requires Pillow — use demos venv)
docs/demos/.venv/bin/python docs/assets/split_composites.py
```

### Logo

| File | Notes |
|------|--------|
| [panels/tekton-dag-logo-2d.png](panels/tekton-dag-logo-2d.png) | Copy of the logo sheet |

### “Related illustrations” four-panel set

| Position | File |
|----------|------|
| Top-left | [panels/related-illustrations-four-01-tl.png](panels/related-illustrations-four-01-tl.png) |
| Top-right | [panels/related-illustrations-four-02-tr.png](panels/related-illustrations-four-02-tr.png) |
| Bottom-left | [panels/related-illustrations-four-03-bl.png](panels/related-illustrations-four-03-bl.png) |
| Bottom-right | [panels/related-illustrations-four-04-br.png](panels/related-illustrations-four-04-br.png) |

### “Tekton concepts” four-panel set

| Position | File |
|----------|------|
| Top-left | [panels/tekton-concepts-four-01-tl.png](panels/tekton-concepts-four-01-tl.png) |
| Top-right | [panels/tekton-concepts-four-02-tr.png](panels/tekton-concepts-four-02-tr.png) |
| Bottom-left | [panels/tekton-concepts-four-03-bl.png](panels/tekton-concepts-four-03-bl.png) |
| Bottom-right | [panels/tekton-concepts-four-04-br.png](panels/tekton-concepts-four-04-br.png) |

### Nine-panel infographic (row-major: r1 = top row)

| # | File |
|---|------|
| 1 | [panels/infographic-nine-01-r1c1.png](panels/infographic-nine-01-r1c1.png) |
| 2 | [panels/infographic-nine-02-r1c2.png](panels/infographic-nine-02-r1c2.png) |
| 3 | [panels/infographic-nine-03-r1c3.png](panels/infographic-nine-03-r1c3.png) |
| 4 | [panels/infographic-nine-04-r2c1.png](panels/infographic-nine-04-r2c1.png) |
| 5 | [panels/infographic-nine-05-r2c2.png](panels/infographic-nine-05-r2c2.png) |
| 6 | [panels/infographic-nine-06-r2c3.png](panels/infographic-nine-06-r2c3.png) |
| 7 | [panels/infographic-nine-07-r3c1.png](panels/infographic-nine-07-r3c1.png) |
| 8 | [panels/infographic-nine-08-r3c2.png](panels/infographic-nine-08-r3c2.png) |
| 9 | [panels/infographic-nine-09-r3c3.png](panels/infographic-nine-09-r3c3.png) |

## Using in Markdown (GitHub / docs)

Paths are relative to the doc file. From a file under `docs/`:

```markdown
![Tekton DAG logo](assets/panels/tekton-dag-logo-2d.png)
![Concept](assets/panels/tekton-concepts-four-01-tl.png)
```

From the repository root `README.md`:

```markdown
![Logo](docs/assets/panels/tekton-dag-logo-2d.png)
```

## Using on GitHub Pages

The site publishes the whole `docs/` tree, so the same paths work from pages under `docs/` (e.g. `assets/panels/...`).

## Script options

- **`--force-quad-logo`** — if the logo sheet is actually a 2×2 composite of 512×512 tiles, split into `panels/logo-sheet-quad-01-tl.png` … instead of copying one file.
