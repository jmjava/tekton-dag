---
docgen:
  project:
    env_file: ../../.env
    discovery:
      auto_visual_map: false
    timestamps:
      engine: whisper
    narration_from_source:
      model: gpt-4o-mini
      temperature: 0.65
      max_context_bytes: 120000
      hints:
        - >-
          Ground every script in the Jul 2026 tree: four pipelines (bootstrap, PR, merge, promote),
          M13 foundations shipped, M14 operator default-on (Stack/StackRun/Team CRs).
        - >-
          Do not frame milestone 13 as entirely future work. Say foundations are shipped and name
          only remaining open items when discussing production hardening.
        - >-
          The Kubernetes operator under operator/ is CRD-primary (Stack + StackRun + Team,
          tektondag.io/v1alpha1). Flask STACKRUN_VIA_CRD and Helm operator.enabled default on.
        - >-
          Demo video for this bundle is Manim + TTS + ffmpeg compose only (current docgen). Do not
          narrate VHS, ttyd, or terminal-tape capture as a pipeline stage.
        - >-
          Timestamps for this bundle must use Whisper (timestamps.engine: whisper). Do not use the
          local silencedetect aligner for shippable demos.
        - >-
          Regression entrypoint is scripts/run-regression-agent.sh (Phase 1 + pytest + Playwright +
          stack-dag-verify + Newman when a cluster is wired).
      context:
        paths:
          - README.md
          - AGENTS.md
          - docs/REGRESSION.md
          - milestones/milestone-13.md
          - milestones/milestone-14.md
          - operator/README.md
        globs: []
    manim_scene_generation:
      hints:
        - >-
          AUDIO-FIRST: scenes are generated only after Whisper timing.json exists for this segment.
          Design pages from narration + timing words; every box label MUST be a short phrase copied
          from spoken narration (same tokens Whisper lists). If it is not spoken, do not show it.
        - >-
          SUBJECT BEATS: hold the board across sentences on the same topic; reveal a new
          spoken-phrase label when the topic shifts. Coverage of beats matters — not a blind
          label count. Never invent unspoken diagram terms.
        - >-
          Do not invent diagram-only terms (Originator, Demo-fe, etc.) unless those exact words are
          spoken. Prefer pages of short rows; ASCII labels only (use -> not unicode). Leave wait_word
          unset so scene-compile binds labels to Whisper word indices.
      context:
        paths:
          - docs/demos/hints/manim-scene-specs.md
        globs: []
    concat:
      full-demo:
        - "01"
        - "02"
        - "03"
        - "04"
        - "05"
        - "06"
        - "07"
        - "08"
        - "09"
        - "10"
        - "11"
        - "12"
        - "13"
      full-demo-complete:
        - "01"
        - "02"
        - "03"
        - "04"
        - "05"
        - "06"
        - "07"
        - "08"
        - "09"
        - "10"
        - "11"
        - "12"
        - "13"
        - "14"
        - "15"
        - "16"
        - "17"
        - "18"
        - "19"
      platform-core:
        - "01"
        - "02"
        - "03"
        - "04"
        - "05"
        - "06"
        - "07"
---

# Project context (tekton-dag docgen)

Body text is optional; **`docgen yaml-generate`** merges the YAML above into
`docs/demos/docgen.yaml`. Re-run after editing this file.
