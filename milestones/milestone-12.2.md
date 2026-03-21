# Milestone 12.2: Documentation sync and archive

> **Part A — Completed.** Hygiene milestone: single source of truth for where docs live, stale pointers removed, obsolete session plans archived.  
> **Part B — Completed.** Narrative documentation and **demo videos** for **regression testing** and **Management GUI** design/extension (M12.2 extension).

## Part A — Goal (completed)

Keep documentation **in sync** with the current codebase and milestone status: root [README](../README.md), [docs/README](../docs/README.md), and milestone banners that contradicted reality. Move **obsolete** material into [docs/archive/](../docs/archive/) (historical reference only).

### Part A — Scope (completed)

- Root README milestone table: accurate M8 status, M12.2 row, chronological order, “Next up” line.
- `docs/README.md`: documentation map (active vs archive), current pointers (CUSTOMIZATION, MAINTENANCE, demos, GitHub Pages, multi-team architecture); remove stale “Planned: M4/M5” footer.
- [milestones/milestone-11.md](milestone-11.md): header status **Completed** (was still “Planned”).
- [milestones/milestone-8.md](milestone-8.md): banner aligned with partial delivery + GitHub Pages link.
- Archive [docs/archive/next-session-plan.md](../docs/archive/next-session-plan.md) (M7-era scratchpad).
- Optional cross-link fixes: [demo-playbook.md](../docs/demo-playbook.md), milestone-8 “make demos” vs `docs/demos/generate-all.sh` if still inconsistent.

### Part A — Success criteria

- [x] `docs/archive/` exists with README explaining purpose.
- [x] Obsolete `next-session-plan.md` moved under archive; references updated.
- [x] Root README and `docs/README.md` list current milestones and doc map.
- [x] No broken relative links from moved files (grep verified).

---

## Part B — Extension: regression docs + GUI videos (completed)

### Goal

- **Documentation** operators and contributors can follow for **what “full regression” means** and **how to extend the Management GUI** for more Tekton interactions.
- **Video plan** (and eventually assets) aligned with [M8](milestone-8.md): segments for regression walkthrough, GUI architecture, and extension pattern.
- **Team onboarding:** baggage/header libraries per runtime and a **checklist for new application stacks** (linked below).

### Deliverables

| Item | Location |
|------|----------|
| Testing / regression narrative | [docs/TESTING-AND-REGRESSION-OVERVIEW.md](../docs/TESTING-AND-REGRESSION-OVERVIEW.md) |
| GUI design & extension guide | [docs/MANAGEMENT-GUI-EXTENSION.md](../docs/MANAGEMENT-GUI-EXTENSION.md) |
| Demo shot list + asset names | [docs/demos/segments-m12-2-regression-gui.md](../docs/demos/segments-m12-2-regression-gui.md) |
| Playbook rows | [docs/demo-playbook.md](../docs/demo-playbook.md) §1 (when segments exist) |
| Team stacks + baggage libraries | [docs/TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md](../docs/TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md) — `libs/*` header propagation by framework; new stack / team wiring checklist |

### Part B — Success criteria

- [x] Overview and extension docs committed; demo segment markdown committed.
- [x] **Videos** composed via M8 toolchain (`compose.sh` **VHS** terminal renders + TTS): `12-regression-suite`, `13-management-gui-architecture`, `14-gui-tekton-extension` under `docs/demos/recordings/` (narration in `docs/demos/narration/12–14*.md`; regenerate MP3 with `docs/demos/generate-narration.py` when narration changes).
- [x] **GitHub Pages** [docs/index.html](../docs/index.html) updated with playable entries for segments 12–14.
- [x] `generate-all.sh` runs core compose then **12–14** and optional `full-demo-with-m12-2.mp4` when all segments exist.
- [x] **Shell script hygiene:** [docs/SCRIPTS.md](../docs/SCRIPTS.md) indexes all `scripts/*.sh`; [scripts/README.md](../scripts/README.md) and [scripts/archive/README.md](../scripts/archive/README.md) document entrypoints and archive policy (aligned with [docs/archive/](../docs/archive/)).
- [x] **Team onboarding (stacks + baggage):** [docs/TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md](../docs/TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md) committed; cross-linked from [docs/README.md](../docs/README.md), [CUSTOMIZATION.md](../docs/CUSTOMIZATION.md), [DAG-AND-PROPAGATION.md](../docs/DAG-AND-PROPAGATION.md), and root [README](../README.md) (M12 row).
- [ ] Optional: extend `docs/demos/animations/timing.json` only if Manim scenes are added for 12–14 (not required for VHS-only segments); richer TTS tuning anytime via `generate-narration.py`.

## References

- Prior note in [milestone-12.md](milestone-12.md) (deferred archive of `next-session-plan.md`) — addressed in Part A.
- Regression commands: [docs/REGRESSION.md](../docs/REGRESSION.md), [scripts/run-regression-agent.sh](../scripts/run-regression-agent.sh).
- Script catalog: [docs/SCRIPTS.md](../docs/SCRIPTS.md).
- Team stacks & baggage libs: [docs/TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md](../docs/TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md).
