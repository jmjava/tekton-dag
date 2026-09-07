# Milestone 16 — Control-plane follow-ons

**Status:** Not started — blocked on M15 landing.

**Goal:** Finish the remaining dual sources of truth after M15 hygiene. Still **no new CRD kinds**.

## Checklist

- [ ] Flask `StackResolver` and GUI `TeamRegistry` read **Team CRs** when present; Git `teams/*/team.yaml` remains the GitOps source that `apply-stack-crs.sh` / `package.sh` mirror
- [ ] Stack validating webhook in-cluster (certs + `ValidatingWebhookConfiguration`); Kind/Helm `ENABLE_WEBHOOKS=true` only with those certs
- [ ] Retire `--pipeline-run` / Flask `STACKRUN_VIA_CRD=false` once every documented cluster path runs the operator
- [ ] `stack-pr-continue` as a field (or new StackRun of `mode=pr`) — not a new CRD
- [ ] Demo **hints** already describe default-on; rebuild **spoken** `docs/demos/narration/*.md` + MP4s via `cd docs/demos && docgen rebuild-after-audio` (do not `compose` alone)
- [ ] S34 intercept E2E remains a separate stop — do not start unless explicitly requested

## Exit criteria

1. GUI/Flask team list matches Team CRs applied from Git YAML.
2. Webhook denies an invalid Stack in Kind with certs installed; Kind without certs still does not apply Fail-closed admission.
3. Escape hatches removed or documented as unsupported.
4. Narration lint + `docgen validate --pre-push` green after the audio rebuild.

## Do not

- Add CRs for intercepts, hooks, registries, promote, compile images, webhooks, Neo4j, or isolation-eval (see [M14](milestone-14.md)).
- Edit spoken narration Markdown without rebuilding Manim/VHS/compose.
