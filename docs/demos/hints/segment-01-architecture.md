---
docgen:
  segment:
    create: true
    id: "01"
    stem: 01-architecture
  wiring:
    visual:
      type: manim
      scene: StackDAGScene
      source: StackDAGScene.mp4
    narration:
      hints:
      - >-
          Open with what tekton-dag is today: stack-aware CI/CD on Tekton that models apps
          as a DAG with dependency edges and propagation roles.
      - >-
          Name the four pipelines clearly: bootstrap, PR (intercept), merge/release, and
          promote (stack-promote + stacks/registries.yaml). Promote is shipped with M13
          foundations — not future work.
      - >-
          Mention the Flask orchestrator as webhook/API brain. Runs become StackRun CRs
          reconciled by the operator (segment 19); Helm operator.enabled defaults on.
      - >-
          Cover polyglot stacks, hook tasks, management GUI, Helm multi-team, Tekton
          Results + Neo4j briefly as the high-level picture.
      context:
        paths:
        - README.md
        - milestones/milestone-13.md
        - milestones/milestone-14.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Title tekton-dag, then DAG of demo-fe -> demo-bff -> demo-api with propagation
          roles.
      - >-
          Four pipeline boxes: Bootstrap, PR, Merge, Promote. Small callout CRD-primary
          path (StackRun) as the default create path.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-01-architecture.md
---

# Narration focus (segment 01 — 01-architecture)

Architecture overview. Emphasize four pipelines including promote; StackRun is the default create path.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
