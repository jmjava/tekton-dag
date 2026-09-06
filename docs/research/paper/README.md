# IEEE paper draft (tool demonstration / workshop)

Source for a **4-page** IEEE conference paper aimed at the [ICSE 2027 Tool Demonstration](https://conf.researchr.org/track/icse-2027/icse-2027-demonstrations) track. The same text can be retargeted to [SESoS](https://conf.researchr.org/home/icse-2027/sesos-2027) by rewriting the introduction in systems-of-systems language (see [../venues.md](../venues.md)).

This is a **pre-submission draft**. It is not camera-ready: affiliation, ORCID, and the 3–5 minute YouTube URL are placeholders.

## Files

| File | Role |
|------|------|
| `main.tex` | IEEEtran `10pt,conference` body (manual `thebibliography` to keep page count predictable) |
| `refs.bib` | Same records for BibTeX / later expansion to 8 pages |
| `Makefile` | `pdflatex` build |

Do **not** pass the `compsoc` option (ICSE CFP). Page cap is **inclusive of references**; extra pages cannot be purchased.

## Build

```bash
cd docs/research/paper
make          # pdflatex (twice)
make bib      # optional: switch workflow if you convert cites to \cite + BibTeX
```

Requires a TeX distribution with `IEEEtran.cls` (TeX Live `texlive-publishers` or equivalent). The checked-in `main.pdf` is a **3-page** compile of the current draft (limit is 4 pages including references).

## Before HotCRP

1. Insert YouTube URL at the end of the abstract (CFP requirement).
2. Fill ORCID and affiliation.
3. Confirm PDF ≤ 4 pages and IEEE margins (no font-size tricks; those are desk rejects).
4. Freeze a git tag and cite it in Section IV.
5. Re-read [../contributions.md](../contributions.md) so no sentence overclaims evaluation.

## Dual-use with SESoS

If the demo paper is submitted, do not upload this PDF unchanged to a workshop. A SESoS short paper should be a distinct text (experience / SoS framing). High-quality SESoS papers may be invited to an ASE journal special issue; that is a later expansion, not this 4-pager.
