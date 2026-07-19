---
docgen:
  segment:
    create: true
    id: "03"
    stem: 03-bootstrap-dataflow
  wiring:
    visual:
      type: manim
      scene: HeaderPropagationScene
      source: HeaderPropagationScene.mp4
    narration:
      hints:
      - >-
          Bootstrap builds and deploys every app: resolve stack, clone repos, compile by
          tool, Kaniko push, deploy-full-stack.
      - >-
          Tie header propagation roles (originator/forwarder/terminal) to the stack graph
          during bootstrap context.
      context:
        paths:
        - README.md
        - pipeline/
        - stacks/
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Pipeline stages as a row flow; second page shows x-dev-session propagation
          through fe/bff/api.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-03-bootstrap-dataflow.md
---

# Narration focus (segment 03 — 03-bootstrap-dataflow)

Bootstrap dataflow + header propagation (Manim only; former mixed/VHS retired).

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
