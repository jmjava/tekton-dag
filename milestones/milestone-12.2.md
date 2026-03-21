# Milestone 12.2: Documentation sync and archive

> **Completed.** Hygiene milestone: single source of truth for where docs live, stale pointers removed, obsolete session plans archived.

## Goal

Keep documentation **in sync** with the current codebase and milestone status: root [README](../README.md), [docs/README](../docs/README.md), and milestone banners that contradicted reality. Move **obsolete** material into [docs/archive/](../docs/archive/) (historical reference only).

## Scope

- Root README milestone table: accurate M8 status, M12.2 row, chronological order, “Next up” line.
- `docs/README.md`: documentation map (active vs archive), current pointers (CUSTOMIZATION, MAINTENANCE, demos, GitHub Pages, multi-team architecture); remove stale “Planned: M4/M5” footer.
- [milestones/milestone-11.md](milestone-11.md): header status **Completed** (was still “Planned”).
- [milestones/milestone-8.md](milestone-8.md): banner aligned with partial delivery + GitHub Pages link.
- Archive [docs/archive/next-session-plan.md](../docs/archive/next-session-plan.md) (M7-era scratchpad).
- Optional cross-link fixes: [demo-playbook.md](../docs/demo-playbook.md), milestone-8 “make demos” vs `docs/demos/generate-all.sh` if still inconsistent.

## Success criteria

- [x] `docs/archive/` exists with README explaining purpose.
- [x] Obsolete `next-session-plan.md` moved under archive; references updated.
- [x] Root README and `docs/README.md` list current milestones and doc map.
- [x] No broken relative links from moved files (grep verified).

## References

- Prior note in [milestone-12.md](milestone-12.md) (deferred archive of `next-session-plan.md`) — addressed here.
