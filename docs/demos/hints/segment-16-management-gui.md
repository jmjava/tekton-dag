---
docgen:
  segment:
    create: true
    id: "16"
    stem: 16-management-gui
  wiring:
    visual:
      type: manim
      scene: ManagementGUITourScene
      source: ManagementGUITourScene.mp4
    narration:
      hints:
      - >-
          Vue3 + Flask management GUI: team switcher, DAG view, pipeline monitoring,
          manual triggers. Injection-status APIs exist for secrets/config; some M13 GUI
          panels still open.
      context:
        paths:
        - README.md
        - milestones/milestone-13.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          GUI panels: Teams, DAG, Runs, Triggers; note injection-status.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-16-management-gui.md
---

# Narration focus (segment 16 — 16-management-gui)

Management GUI tour.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
