# Milestone 16 — Control-plane follow-ons

**Status:** Code-complete except parked S34 (M15 [#19](https://github.com/jmjava/tekton-dag/pull/19); overlay / continueFrom / webhook [#20](https://github.com/jmjava/tekton-dag/pull/20); escape hatches [#21](https://github.com/jmjava/tekton-dag/pull/21); hint polish [#22](https://github.com/jmjava/tekton-dag/pull/22); unused create helpers [#23](https://github.com/jmjava/tekton-dag/pull/23); spoken demo rebuild [#24](https://github.com/jmjava/tekton-dag/pull/24)).

**Goal:** Finish the remaining dual sources of truth after M15 hygiene. Still **no new CRD kinds**.

## Checklist

- [x] Flask `StackResolver` and GUI `TeamRegistry` overlay **Team CRs** when a loader is wired; Git `teams/*/team.yaml` remains the GitOps source that `apply-stack-crs.sh` / `package.sh` mirror
- [x] Kind webhook installer (`scripts/install-operator-webhook-kind.sh`): certs + Service + ValidatingWebhookConfiguration; `ENABLE_WEBHOOKS=true` only with those certs. Helm still does not apply Fail-closed admission by default.
- [x] Retire `--pipeline-run` / Flask `STACKRUN_VIA_CRD=false` (Flask always creates StackRuns; Helm env stays `"true"` for mixed-image rollouts; `--skip-operator` no longer flips the flag)
- [x] `spec.continueFrom` on StackRun + operator `stack-pr-continue` builder; `rerun-pr-from.sh` creates a StackRun
- [x] Demo **hints** already describe default-on; rebuilt **spoken** `docs/demos/narration/*.md` + MP4s via TTS + Manim + `docgen compose` + `docgen validate --pre-push` (segments 01, 08, 18, 19) — [#24](https://github.com/jmjava/tekton-dag/pull/24)
- [ ] S34 intercept E2E remains a separate stop — do not start unless explicitly requested

## Exit criteria

1. GUI/Flask team list matches Team CRs applied from Git YAML (overlay).
2. Webhook installer exists; Kind without the installer still does not apply Fail-closed admission.
3. Escape hatches removed: `--pipeline-run` and `STACKRUN_VIA_CRD=false` are unsupported.
4. Narration lint + `docgen validate --pre-push` green after the audio rebuild.

## Do not

- Add CRs for intercepts, hooks, registries, promote, compile images, webhooks, Neo4j, or isolation-eval (see [M14](milestone-14.md)).
- Edit spoken narration Markdown without rebuilding Manim/VHS/compose.
