---
docgen:
  segment:
    create: true
    id: "19"
    stem: 19-kubernetes-operator
  wiring:
    visual:
      type: manim
      scene: OperatorCRDScene
      source: OperatorCRDScene.mp4
    narration:
      hints:
      - >-
          Problem: Flask creating PipelineRuns directly is less GitOps-friendly than
          desired-state CRs.
      - >-
          CRDs: Stack (validate/topo status) vs StackRun (mode pr|bootstrap|merge|promote
          -> PipelineRun).
      - >-
          Flow: GitHub/API -> Flask (HMAC+resolve) -> StackRun -> tekton-dag-operator ->
          PipelineRun (orphaned on delete for Results history).
      - >-
          Enablement: STACKRUN_VIA_CRD + Helm operator.enabled (default off). Golden
          Python↔Go PipelineRun builders.
      - >-
          Status: foundations shipped under operator/; not default runtime yet.
      context:
        paths:
        - operator/README.md
        - milestones/milestone-14.md
        - orchestrator/stackrun_builder.py
        - docs/demos/hints/narration-tts.md
        - docs/demos/hints/manim-scene-specs.md
    manim_scene:
      hints:
      - >-
          Flow diagram pages: Webhook/API -> Flask -> StackRun -> Operator -> PipelineRun;
          side boxes Stack CRD and StackRun CRD; footer Not default-on.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-19-kubernetes-operator.md
---

# Narration focus (segment 19 — 19-kubernetes-operator)

Kubernetes operator CRD-primary deep-dive (new segment).

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
