---
docgen:
  segment:
    create: true
    id: "14"
    stem: 14-customization
  wiring:
    visual:
      type: manim
      scene: CustomizationScene
      source: CustomizationScene.mp4
    narration:
      hints:
      - >-
          Config-driven extension: stacks/schema.json, hook tasks, secrets/config blocks
          in stack YAML (M13 foundations), Helm values — without forking core pipelines.
      context:
        paths:
        - README.md
        - stacks/schema.json
        - milestones/milestone-13.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Schema -> stack YAML -> hooks/secrets/config -> Helm values flow.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-14-customization.md
---

# Narration focus (segment 14 — 14-customization)

Customization points.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
