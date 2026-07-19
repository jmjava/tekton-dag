---
docgen:
  segment:
    create: true
    id: "04"
    stem: 04-pr-pipeline
  wiring:
    visual:
      type: manim
      scene: PRPipelineScene
      source: PRPipelineScene.mp4
    narration:
      hints:
      - >-
          PR webhook -> orchestrator resolves changed app -> PipelineRun (or StackRun if
          CRD path on) in PR mode builds only the changed service.
      - >-
          Deploy intercept beside baseline; tests run with x-dev-session so traffic hits
          the PR build.
      context:
        paths:
        - README.md
        - milestones/milestone-13.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Webhook -> resolve -> PR PipelineRun; changed app highlighted; intercept sidecar
          vs baseline.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-04-pr-pipeline.md
---

# Narration focus (segment 04 — 04-pr-pipeline)

PR pipeline deep-dive as Manim (replaces former VHS tape).

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
