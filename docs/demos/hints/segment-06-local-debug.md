---
docgen:
  segment:
    create: true
    id: "06"
    stem: 06-local-debug
  wiring:
    visual:
      type: manim
      scene: LocalDebugScene
      source: LocalDebugScene.mp4
    narration:
      hints:
      - >-
          Debug failed PR tests locally with mirrord: laptop IDE receives mirrored cluster
          traffic with real headers and payloads.
      context:
        paths:
        - README.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Laptop <-> mirrord tunnel <-> cluster stack; breakpoint callout on local
          process.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-06-local-debug.md
---

# Narration focus (segment 06 — 06-local-debug)

Local debug with mirrord.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
