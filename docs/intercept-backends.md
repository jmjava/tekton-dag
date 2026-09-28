# Intercept backends: mirrord in CI, Telepresence on the laptop

**Status (2026-09-27):** mirrord is the only intercept backend the PR pipeline
runs in CI and the default everywhere (`intercept-backend=mirrord`). Until this
change neither backend had ever routed a header request to a PR pod in CI;
section 4 explains how mirrord's green was a race and what now proves routing. The
in-cluster Telepresence sidecar task is kept as **experimental** and is not
exercised by CI. Telepresence remains supported as a **laptop** workflow.

This page records why, with the evidence, so the decision can be revisited
with facts rather than memory.

## 1. What the PR pipeline has to prove

The product contract for a PR run is:

1. A request carrying the PR's session header (for example
   `x-dev-session: pr-42`) that hits an intercepted app's Kubernetes Service is
   served by that app's **PR pod**.
2. A request without the header is served by the **live baseline**, untouched.
3. The header (and `baggage`) is copied hop-to-hop through the stack.

Three tasks check this: `validate-stack-propagation` (3 and, since this change,
1 and 2), `validate-original-traffic` (2), and `run-tests`.

## 2. The Telepresence in-cluster path never worked

Runs of `intercept-e2e.yml` on `main` were green for the `telepresence` matrix
leg from 2026-09-16 to 2026-09-21 and the session notes from February and March
2026 say "E2E with Telepresence intercepts passing". Reading the artifacts and
the task as it existed on `main` shows the pass was vacuous:

| Fact | Evidence |
| --- | --- |
| The PR pod never ran the app. | `tasks/deploy-intercept.yaml` on `main` started the built image with `sh -c 'while true; do echo "PR build for ${APP}"; sleep 30; done'`. It could not answer an HTTP request. |
| The sidecar had no Telepresence CLI. | The sidecar image was `ghcr.io/telepresenceio/tel2:2.20.0`, the traffic-agent image. It ships one binary, `traffic`; `telepresence` is not present (`docker run --rm --entrypoint sh ghcr.io/telepresenceio/tel2:2.20.0 -c 'command -v telepresence'` prints nothing). `telepresence helm install` failed with *not found* and the container exited after its initial `sleep 10`, during which the pod was briefly `Ready`, so `kubectl wait` passed. |
| Validation was warn-only. | `validate-stack-propagation` printed `HOP 1 demo-fe (originator) [INTERCEPTED]: NOT CONFIRMED (header required at this hop)` and then `Propagation validation complete.` with exit 0. Artifact: run `35612789828`, `artifacts/telepresence/pr-pod-logs.txt`. |
| Green turned red the day the check became honest. | `d07635f` / `5ef46c7` (2026-09-26) made hop validation fail-closed. The next `main` run (`0c75b06`, 2026-09-27) failed. Nothing in Telepresence changed. |

So "Telepresence used to work" is true for the laptop workflow, where a
developer runs `telepresence intercept` against the cluster and traffic lands
on a local process. It was never true for the in-cluster sidecar variant the
pipeline used; that variant reported success without doing anything.

## 3. What was tried on PR #109 to make the in-cluster path real

Commits on `fix/post-deploy-checks`, in order, each verified by a full CI run
(about 15 minutes each):

| Attempt | Result |
| --- | --- |
| Real CLI image (`build-images/Dockerfile.telepresence`, Telepresence 2.32.1), sidecar in the PR pod. | `connector.CreateIntercept: grpc: the client connection is closing`. 2.32.1 could not create intercepts from inside this cluster at all. |
| Separate privileged client pod (own ServiceAccount, tun device, `HOME=/tmp`), still 2.32.1. | Same gRPC error. |
| Downgrade to 2.25.0 (matching the traffic manager). | Intercept created. Header-matched request to the Service hung (`HTTP 000`); unmatched request passed. |
| `--never-proxy <PR pod IP>/32` and a local `socat` relay to the PR pod. | Same hang. |
| Whole-port TCP intercept (`--mechanism tcp`) with a header router in front. | Steals *all* traffic to the port, which violates contract item 2, and Telepresence reported `container port 80 is already intercepted`. Rejected. |
| `--plaintext` (HTTP intercepts default to TLS toward the handler; the PR pod is plaintext nginx). | Intercept `ACTIVE`, filter `HTTP requests with header 'X-Dev-Session: pr-95'`. Smoke probe: headered request `HTTP 000` then `502`, unmatched `200`. Root cause visible only once log collection stopped truncating to 10 lines (`368b117`): `connector/session : root session exited with error: exec: "iptables": executable file not found in $PATH`. The client image (`bitnami/kubectl`) has no `iptables`, so the client's root session (the tunnel that carries intercepted requests back to the handler) never started. |

Other costs of the in-cluster sidecar design that mirrord does not have:

- Injecting the traffic-agent restarts the live baseline Deployment.
- The client needs `NET_ADMIN`, a tun device, root, and a privileged namespace.
- Client and traffic-manager versions must match closely; 2.32 vs 2.25 was
  enough to break intercept creation.

At that point the choice was: keep iterating on a design the project had never
had working, or ship the backend that already met the contract. We chose the
latter.

## 4. Why mirrord is trusted

`tasks/deploy-intercept-mirrord.yaml` runs the built image as the real app in
the PR pod and uses `mirrord exec` with `http_filter.header_filter` in steal
mode, relaying matched requests through `socat` to the PR pod IP.

Its green runs were audited too, and they were **also false positives** until
this change. The proxy pod ran as the namespace `default` ServiceAccount, and
`mirrord exec` died within a second on
`deployments.apps "demo-fe" is forbidden: User "system:serviceaccount:staging:default"`.
The deploy step only checked `kubectl wait --for=condition=Ready`; a container
with no readiness probe is Ready the instant it runs, so the wait usually
caught that one-second window and printed `Intercept active`. Run
`36367430488` lost the race (`Restart Count: 4`) and exposed it. Downstream,
`/propagation` is served identically by the baseline and the PR pod and simply
echoes the header it received, so `PASS — REACHED session=pr-N` alone never
proved which pod answered.

So as of 2026-09-27 **neither backend had ever routed a header request to a
PR pod in CI**. mirrord is the one worth finishing because its failure is a
plain RBAC gap and it needs no privileged client, no restart of the live
Deployment, and no version coupling. Fixes in this PR:

- The proxy pod runs as `mirrord-intercept` (ServiceAccount + namespace Role:
  read pods/deployments/replicasets, create the agent Job), created by
  `scripts/install-mirrord-intercept-rbac.sh`, which the runners call.
- The deploy step fails closed on the first mirrord error line, any restart,
  or a proxy that is not serving (`restartPolicy: Never`; direct probe through
  socat to the PR pod, or 30 s Running and error-free).
- `validate-stack-propagation` adds a **routing proof**, fail-closed, per
  intercepted app:

1. `GET <service>/propagation?probehit<id>` **with** the header. The id must
   appear in the PR pod's access log (nginx logs every request line to stdout;
   the log is read through the Kubernetes API with the task's ServiceAccount,
   which already has `pods/log`).
2. `GET <service>/propagation?probemiss<id>` **without** the header. The id
   must **not** appear in the PR pod's log.

If the intercept silently does nothing, step 1 fails. If it steals everything,
step 2 fails. The pipeline passes `deployed-pods` (app → PR pod name) from
`deploy-intercepts-result` to the validator for this purpose.

## 5. What changed in the repository

- `.github/workflows/intercept-e2e.yml`: matrix is `[mirrord]`; the
  Telepresence traffic-manager install step is gone.
- Default `intercept-backend` is `mirrord` in `pipeline/stack-pr-pipeline.yaml`,
  `pipeline/stack-pr-continue-pipeline.yaml`, `scripts/run-product-intercept-e2e.sh`,
  `scripts/run-e2e-with-intercepts.sh`, the orchestrator (`app.py`,
  `pipelinerun_builder.py`, `k8s-deployment.yaml`), the operator
  (`internal/pipeline/builder.go`), and the Helm chart (`interceptBackend`).
- `tasks/validate-propagation.yaml`: new `deployed-pods` param and the routing
  proof above.
- `scripts/run-product-intercept-e2e.sh`: `--tail=-1` on log collection so
  artifacts carry full step output.

Kept, marked experimental, not run by CI:

- `tasks/deploy-intercept.yaml` (in-cluster Telepresence client pod, 2.25.0,
  `--http-header ... --plaintext`).
- `build-images/Dockerfile.telepresence`,
  `scripts/install-telepresence-traffic-manager.sh`.

Selecting it explicitly (`--intercept-backend telepresence` or the pipeline
param) still works and now fails closed at the deploy step if routing is not
live.

## 6. Telepresence on the laptop (supported)

This is the workflow Telepresence is designed for and the one people remember
working:

```bash
./scripts/install-telepresence-traffic-manager.sh          # once per cluster
telepresence connect --namespace staging
telepresence intercept demo-fe --port 8080:80 \
  --http-header x-dev-session=pr-42
# run demo-fe locally on :8080, attach a debugger,
# send a request with x-dev-session: pr-42 through the cluster entry point
telepresence leave demo-fe
telepresence quit
```

See `.vscode/README.md` and `docs/demo-playbook.md` for the step-debug flow;
mirrord works the same way from the laptop (`mirrord exec`).

## 7. Reopening the in-cluster Telepresence path

The last known blocker is small: the client image lacks `iptables`, so the
Telepresence root session exits at connect time (section 3, last row). The
next step is to add `iptables` to `build-images/Dockerfile.telepresence`
(the client already runs privileged as root with a tun device), re-run
`--intercept-backend telepresence`, and read the deploy step's smoke probe
and daemon log dump (`/tmp/.cache/telepresence/logs/*.log`). Prefer a local
kind cluster over 15-minute CI cycles. Any fix must pass the routing proof in
section 4 for both matched and unmatched traffic before the matrix entry is
restored.
