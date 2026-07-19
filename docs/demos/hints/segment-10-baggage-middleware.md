---
docgen:
  segment:
    create: true
    id: "10"
    stem: 10-baggage-middleware
  wiring:
    visual:
      type: manim
      scene: BaggageMiddlewareScene
      source: BaggageMiddlewareScene.mp4
    narration:
      hints:
      - >-
          Baggage middleware auto-propagates x-dev-session across frameworks; roles
          originator/forwarder/terminal/standalone.
      context:
        paths:
        - README.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Five framework boxes under propagation role headers.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-10-baggage-middleware.md
---

# Narration focus (segment 10 — 10-baggage-middleware)

Baggage middleware libraries.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
