---
docgen:
  segment:
    create: true
    id: "02"
    stem: 02-quickstart
  wiring:
    visual:
      type: manim
      scene: QuickstartScene
      source: QuickstartScene.mp4
    narration:
      hints:
      - >-
          Walk Kind-with-registry, install Tekton, Helm install of tekton-dag, and first
          bootstrap or health check — spoken as diagram steps, not terminal capture.
      - >-
          Point to DO-THIS-LOCAL or README quickstart paths. Keep commands as spoken
          phrases without backticks.
      context:
        paths:
        - README.md
        - DO-THIS-LOCAL.md
        - docs/demos/hints/narration-tts.md
    manim_scene:
      hints:
      - >-
          Sequential pages: Kind cluster -> Tekton install -> Helm release ->
          Healthz/Readyz green.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
          - docs/demos/hints/segment-02-quickstart.md
---

# Narration focus (segment 02 — 02-quickstart)

Local quickstart as Manim steps (no VHS).

Keep spoken output plain prose (see narration-tts.md). Bullets here steer narration-generate / scene-spec-generate only.
