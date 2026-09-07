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

### Dual intercept backends

- **Context:** header match for PR traffic.
- **What we learned:** Telepresence `--http-match` and mirrord `header_filter` can both isolate HTTP; cleanup and privilege models differ.
- **Peer copy:** the contribution is pipeline-placed intercepts + unmatched probes, not a new dataplane. Report which backend the *site* standardized on.
