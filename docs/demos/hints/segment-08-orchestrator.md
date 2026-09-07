---
docgen:
  segment:
    create: true
    id: "08"
    stem: 08-orchestrator
  wiring:
    visual:
      type: manim
      scene: OrchestratorAPIScene
      source: OrchestratorAPIScene.mp4
    narration:
      hints:
      - >-
          Flask orchestrator on 8080: healthz/readyz, stacks API, POST /api/run modes
          including promote.
      - >-
          Orchestrator still owns webhook HMAC (fail-closed when named Secret missing) and
          stack resolve. Flask always creates StackRun CRs; the operator reconciles
          them to PipelineRuns (see segment 19).
      context:
        paths:
        - README.md
        - milestones/milestone-13.md
        - milestones/milestone-14.md
        - orchestrator/
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          API boxes: healthz, stacks, run(pr|bootstrap|merge|promote); branch Direct
          PipelineRun vs StackRun CRD path.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-08-orchestrator.md
---

# Narration focus (segment 08 — 08-orchestrator)

Orchestrator API; HMAC + optional CRD path.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
