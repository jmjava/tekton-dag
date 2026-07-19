---
docgen:
  segment:
    create: true
    id: "18"
    stem: 18-roadmap-forward
  wiring:
    visual:
      type: manim
      scene: RoadmapScene
      source: RoadmapScene.mp4
    narration:
      hints:
      - >-
          Retarget: do NOT pitch M13 as what we build next. M13 foundations are shipped
          (HMAC, secrets/config + status APIs, timeouts/retries/classifier/profiles,
          promote+registries).
      - >-
          Remaining M13 open items only: intercept secret wiring, Helm appConfig/ESO
          templates, GUI panels, Prometheus/cost labels, cross-cluster deploy,
          Results/Neo4j backup polish.
      - >-
          Post-M14 follow-ons: default-on operator.enabled after soak, Team CR, GUI native
          StackRun views / promote approve via StackRun.spec.approvedBy, Stack admission
          webhook, retire direct PipelineRun path once CRD is default.
      context:
        paths:
        - milestones/milestone-13.md
        - milestones/milestone-14.md
        - operator/README.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Two columns: M13 open items | M14 follow-ons. Title Whats next — not Milestone
          13 preview.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-18-roadmap-forward.md
---

# Narration focus (segment 18 — 18-roadmap-forward)

Roadmap forward: remaining open work after shipped M13/M14 foundations.

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
