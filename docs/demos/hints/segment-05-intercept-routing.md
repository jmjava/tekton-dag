---
docgen:
  segment:
    create: true
    id: "05"
    stem: 05-intercept-routing
  wiring:
    visual:
      type: manim
      scene: InterceptRoutingScene
      source: InterceptRoutingScene.mp4
    narration:
      hints:
      - >-
          Contrast baseline traffic (no header) vs PR traffic (x-dev-session) through the
          same ingress and services.
      - >-
          Telepresence or mirrord intercept; note M13 open: intercept secret wiring still
          incomplete while stack secrets on full deploy are shipped.
      context:
        paths:
        - README.md
        - milestones/milestone-13.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Two colored request paths through fe/bff/api; green path diverts to PR pod.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-05-intercept-routing.md
---

# Narration focus (segment 05 — 05-intercept-routing)

Intercept routing visualization.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
