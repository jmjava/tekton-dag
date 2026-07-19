# Narration style for TTS (tekton-dag)

When drafting **`narration/*.md`** for `docgen tts` / validate:

- **Plain spoken prose** — no markdown headings, bullets, or inline backticks
  (narration lint rejects backtick-wrapped code).
- Prefer phrasing like: open the docgen.yaml file, run the regression agent script —
  not fenced or backtick-wrapped command names.
- Keep sentences short enough for calm TTS.
- Pronounce clearly: Tekton, Kubernetes, Helm, Newman, pytest, Neo4j, Manim,
  StackRun, Stack CRD, tektondag.io, Kaniko, mirrord, Telepresence.
- Say “x-dev-session” as “ex dash dev dash session” on first use if needed.
- Do not mention segment numbers, target durations, or stage directions in spoken text.
