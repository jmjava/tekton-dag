---
docgen:
  segment:
    create: true
    id: "09"
    stem: 09-multi-team-helm
  wiring:
    visual:
      type: manim
      scene: MultiTeamScene
      source: MultiTeamScene.mp4
    narration:
      hints:
      - >-
          Helm multi-team: per-team releases, scoped ConfigMaps, shared Tasks/Pipelines.
          operator.enabled is off by default.
      context:
        paths:
        - README.md
        - helm/tekton-dag/
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          One cluster, three team namespaces/releases side by side.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-09-multi-team-helm.md
---

# Narration focus (segment 09 — 09-multi-team-helm)

Multi-team Helm.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
