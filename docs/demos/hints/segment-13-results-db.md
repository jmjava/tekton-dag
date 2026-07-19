---
docgen:
  segment:
    create: true
    id: "13"
    stem: 13-results-db
  wiring:
    visual:
      type: manim
      scene: ResultsDBScene
      source: ResultsDBScene.mp4
    narration:
      hints:
      - >-
          Tekton Results watches PipelineRuns/TaskRuns into Postgres; verify-results
          script; history retained when StackRuns orphan PipelineRuns under CRD path.
      context:
        paths:
        - README.md
        - milestones/milestone-14.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          PipelineRun -> Results watcher -> Postgres; note orphan GC preserves history.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-13-results-db.md
---

# Narration focus (segment 13 — 13-results-db)

Tekton Results DB as Manim.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
