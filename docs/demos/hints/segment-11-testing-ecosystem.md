---
docgen:
  segment:
    create: true
    id: "11"
    stem: 11-testing-ecosystem
  wiring:
    visual:
      type: manim
      scene: TestingEcosystemScene
      source: TestingEcosystemScene.mp4
    narration:
      hints:
      - >-
          Newman, pytest, Playwright, Artillery integrated via stack test specs and run-
          stack-tests; orchestrator Newman contracts vs full regression.
      context:
        paths:
        - README.md
        - docs/REGRESSION.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Four testing framework boxes feeding run-stack-tests.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-11-testing-ecosystem.md
---

# Narration focus (segment 11 — 11-testing-ecosystem)

Testing ecosystem as Manim (replaces VHS).

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
