#!/usr/bin/env python3
"""
Split composite PNG sheets in docs/assets/ into individual panel images.

Layouts (from pixel dimensions):
  - 1536 x 1024 → 2 x 2 grid (768 x 512)
  - 1536 x 1024, nine panels → 3 x 3 (512 wide; row heights 341, 341, 342)
  - 1024 x 1024 logo sheet → single output (copy), or 2 x 2 if --force-quad-logo

Outputs go to docs/assets/panels/ (git-friendly names for READMEs and demos).
Run from repo root: python3 docs/assets/split_composites.py
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent
PANELS = ASSETS / "panels"


def split_grid_2x2(src: Path, stem: str, start_index: int = 1) -> list[Path]:
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    if w % 2 or h % 2:
        raise ValueError(f"{src}: expected even dimensions for 2x2, got {w}x{h}")
    cw, ch = w // 2, h // 2
    out: list[Path] = []
    idx = start_index
    order = [("tl", 0, 0), ("tr", cw, 0), ("bl", 0, ch), ("br", cw, ch)]
    for suffix, x0, y0 in order:
        crop = im.crop((x0, y0, x0 + cw, y0 + ch))
        path = PANELS / f"{stem}-{idx:02d}-{suffix}.png"
        crop.save(path, optimize=True)
        out.append(path)
        idx += 1
    return out


def split_grid_3x3_1536x1024(src: Path, stem: str) -> list[Path]:
    """3 columns x 3 rows; width 512 each; heights sum to 1024."""
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    if w != 1536 or h != 1024:
        raise ValueError(f"{src}: expected 1536x1024 for 3x3 preset, got {w}x{h}")
    col_w = 512
    row_heights = [341, 341, 342]
    assert sum(row_heights) == h
    out: list[Path] = []
    y0 = 0
    for row, rh in enumerate(row_heights):
        x0 = 0
        for col in range(3):
            crop = im.crop((x0, y0, x0 + col_w, y0 + rh))
            n = row * 3 + col + 1
            path = PANELS / f"{stem}-{n:02d}-r{row + 1}c{col + 1}.png"
            crop.save(path, optimize=True)
            out.append(path)
            x0 += col_w
        y0 += rh
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force-quad-logo",
        action="store_true",
        help="Treat 1024x1024 logo sheet as 2x2 (512x512) instead of one image.",
    )
    args = parser.parse_args()

    PANELS.mkdir(parents=True, exist_ok=True)

    # Source composites (auto-generated filenames from image tools)
    four_related = ASSETS / "a_collection_of_four_digital_illustrations_related.png"
    four_tekton = ASSETS / "a_set_of_four_digital_illustrations_related_to_te.png"
    nine_grid = ASSETS / "a_set_of_nine_informational_and_illustrative_graph.png"
    logo_src = ASSETS / "a_logo_for_tekton_dag_is_displayed_in_a_2d_digit.png"

    generated: list[Path] = []

    if four_related.is_file():
        generated.extend(split_grid_2x2(four_related, "related-illustrations-four"))
    if four_tekton.is_file():
        generated.extend(split_grid_2x2(four_tekton, "tekton-concepts-four"))
    if nine_grid.is_file():
        generated.extend(split_grid_3x3_1536x1024(nine_grid, "infographic-nine"))

    if logo_src.is_file():
        im = Image.open(logo_src)
        w, h = im.size
        if args.force_quad_logo and w == 1024 and h == 1024:
            generated.extend(split_grid_2x2(logo_src, "logo-sheet-quad"))
        else:
            dst = PANELS / "tekton-dag-logo-2d.png"
            shutil.copy2(logo_src, dst)
            generated.append(dst)

    print(f"Wrote {len(generated)} file(s) under {PANELS}")
    for p in sorted(generated):
        print(f"  {p.relative_to(ASSETS)}")


if __name__ == "__main__":
    main()
