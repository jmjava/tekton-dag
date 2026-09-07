# Milestone 16 — Control-plane follow-ons

**Status:** In progress (M15 landed as #19).

**Goal:** Finish the remaining dual sources of truth after M15 hygiene. Still **no new CRD kinds**.

## Checklist

- [x] Flask `StackResolver` and GUI `TeamRegistry` overlay **Team CRs** when a loader is wired; Git `teams/*/team.yaml` remains the GitOps source that `apply-stack-crs.sh` / `package.sh` mirror
- [x] Kind webhook installer (`scripts/install-operator-webhook-kind.sh`): certs + Service + ValidatingWebhookConfiguration; `ENABLE_WEBHOOKS=true` only with those certs. Helm still does not apply Fail-closed admission by default.
- [ ] Retire `--pipeline-run` / Flask `STACKRUN_VIA_CRD=false` once every documented cluster path runs the operator
- [x] `spec.continueFrom` on StackRun + operator `stack-pr-continue` builder; `rerun-pr-from.sh` creates a StackRun
- [ ] Demo **hints** already describe default-on; rebuild **spoken** `docs/demos/narration/*.md` + MP4s via `cd docs/demos && docgen rebuild-after-audio` (do not `compose` alone)
- [ ] S34 intercept E2E remains a separate stop — do not start unless explicitly requested

## Exit criteria

1. GUI/Flask team list matches Team CRs applied from Git YAML (overlay).
2. Webhook installer exists; Kind without the installer still does not apply Fail-closed admission.
3. Escape hatches removed or documented as unsupported.
4. Narration lint + `docgen validate --pre-push` green after the audio rebuild.

## Do not

- Add CRs for intercepts, hooks, registries, promote, compile images, webhooks, Neo4j, or isolation-eval (see [M14](milestone-14.md)).
- Edit spoken narration Markdown without rebuilding Manim/VHS/compose.
