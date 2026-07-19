---
docgen:
  segment:
    create: true
    id: "15"
    stem: 15-regression-suite
  wiring:
    visual:
      type: manim
      scene: RegressionSuiteScene
      source: RegressionSuiteScene.mp4
    narration:
      hints:
      - >-
          Regression via scripts/run-regression-agent.sh: Phase 1 offline checks + pytest;
          with cluster: stack-dag-verify, Playwright GUI, Newman. Prefer this entrypoint
          over ad-hoc scripts.
      context:
        paths:
        - docs/REGRESSION.md
        - scripts/run-regression-agent.sh
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Layered phases: Phase1 offline -> pytest -> cluster DAG verify ->
          Playwright/Newman.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-15-regression-suite.md
---

# Narration focus (segment 15 — 15-regression-suite)

Regression suite as Manim (replaces VHS).

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
