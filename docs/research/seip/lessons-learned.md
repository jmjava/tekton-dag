# Lessons learned (SEIP §6 seed)

Add one short entry when something actually breaks in a real environment. Prefer site incidents. Repo session notes are **seeds only** until they happen on the SEIP site (see Gate 0).

Format:

```
### YYYY-MM — title
- Context:
- What we believed:
- What failed:
- What we changed:
- What a peer org should copy:
```

## Seeds from this repository (not yet site evidence)

### Kind registry topology

- **Context:** compile images pulled inside Kind PipelineRuns.
- **What we believed:** host port `localhost:5001` and in-cluster `localhost:5000` were interchangeable.
- **What failed:** `ImagePullFailed`; Kind containerd redirects `localhost:5000` to `kind-registry` and has no `kind-registry:5000` host entry.
- **What we changed:** publish on the host port, map to `localhost:5000` in pipeline params (`session-notes-2026-02-28.md`).
- **Peer copy:** document the *pod-visible* registry name, not the laptop port.

### Containerize batch status on stdout

- **Context:** parallel Kaniko pods, `wait_for_batch`.
- **What failed:** status lines on stdout were captured as “failures” even when pods succeeded.
- **What we changed:** status to stderr.
- **Peer copy:** Tekton result capture and human logs must not share stdout.

### Intercept agents vs Pod Security

- **Context:** mirrord/Telepresence in-cluster.
- **What failed / constrained:** agents need elevated capabilities (`SYS_ADMIN`, `hostPID`, host mounts); in-task `mirrord exec` is a poor fit without Operator (`docs/mirrord-poc-results.md`).
- **Peer copy:** do not run intercept dataplanes on production nodes; treat original-traffic validation as a required task, not a demo.

### Webhook HMAC fail-closed

- **Context:** M13 GitHub webhooks.
- **What we changed:** unsigned allowed only when no secret is configured; missing named Secret fails closed.
- **Peer copy:** “open for local Kind” vs “fail closed in the site cluster” must be explicit in the paper’s deployment description.

### 2026-09 — Tekton v1.6 hook taskRef names

- **Context:** Kind cluster-ci applied `pipeline/stack-*.yaml` after `install-tekton.sh` used `…/latest/`.
- **What we believed:** `taskRef.name: $(params.pre-build-task)` plus a `when` skip was valid at apply time.
- **What failed:** admission webhook rejected `$()` as a DNS label; bootstrap/PR/merge pipelines would not apply.
- **What we changed:** cluster resolver for hooks; pin Pipelines **v1.6.0** and Triggers **v0.34.0** (S38).
- **Peer copy:** pin Tekton; do not put param substitution in `taskRef.name`; `kubectl apply` the three pipelines on that pin.

### 2026-09 — Kind registry default vs helper

- **Context:** `run-cluster-ci.sh` Newman path, `kind-with-registry.sh` listening on host **:5000**.
- **What we believed:** `IMAGE_REGISTRY` default `localhost:5001` was the Kind host publish address.
- **What failed:** `docker push localhost:5001` connection refused; Phase 2 had already Succeeded.
- **What we changed:** default and cluster-ci publish address **:5000** to match the helper; keep 5001→5000 remap (S39).
- **Peer copy:** one host port, documented next to `kind-with-registry.sh`; do not leave a second default in `common.sh`.

- **Context:** header match for PR traffic.
- **What we learned:** Telepresence `--http-match` and mirrord `header_filter` can both isolate HTTP; cleanup and privilege models differ.
- **Peer copy:** the contribution is pipeline-placed intercepts + unmatched probes, not a new dataplane. Report which backend the *site* standardized on.
