---
docgen:
  segment:
    create: true
    id: "07"
    stem: 07-merge-release
  wiring:
    visual:
      type: manim
      scene: MergeReleaseScene
      source: MergeReleaseScene.mp4
    narration:
      hints:
      - >-
          Merge mode: release version bump strips RC suffix, rebuild/tag release images,
          update mainline deploy.
      - >-
          Promote is a separate shipped pipeline (stack-promote + registries.yaml) for
          pushing release images to target registries — do not call promote future work.
      context:
        paths:
        - README.md
        - milestones/milestone-13.md
        - stacks/registries.yaml
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Merge PipelineRun stages; side box Promote pipeline shipped with
          registries.yaml.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-07-merge-release.md
---

# Narration focus (segment 07 — 07-merge-release)

Merge/release plus shipped promote path.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
