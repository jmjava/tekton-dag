# Intercept backend: mirrord (in-cluster Telepresence removed)

**Status (2026-09-27):** mirrord is the only intercept backend. The in-cluster
Telepresence task, its image, its traffic-manager install script and its
pipeline branch were **removed** (approved 2026-09-27). Until this change
neither backend had ever routed a header request to a PR pod in CI; section 4
explains how mirrord's green was a race and what now proves routing.
Telepresence is not part of this repository any more; developers may still use
it from a laptop with their own install, exactly as they would use `mirrord
exec` locally.

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
  read pods/deployments/replicasets, create the agent Job, **`get`/`create`
  on `pods/portforward`**), created by
  `scripts/install-mirrord-intercept-rbac.sh`, which the runners call.
  mirrord OSS reaches its agent through the Kubernetes port-forward API as a
  WebSocket upgrade; without that verb the agent starts and the proxy dies
  ~17 s later with `failed to switch protocol: 403 Forbidden`. Found on the
  local kind cluster in two minutes, after a CI round-trip had missed it.
- The deploy step fails closed with a positive marker: `RUST_LOG=mirrord=info`
  makes the proxy log `Created agent pod ... pod_name: "mirrord-agent-…"`; the
  step requires that agent pod and the proxy to be Running, with zero
  restarts and no fatal log line (`Failed to create/connect to the created
  mirrord-agent`, `Forbidden`, `Error:`), still true 40 s after the agent
  appeared. `restartPolicy: Never`. The proxy's own IP:port is not probed —
  under the mirrord layer socat's listener is virtual. mirrord's
  `ERROR mirrord::connection: failed to obtain machine ID` is non-fatal
  telemetry noise and is ignored on purpose.
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
  Telepresence traffic-manager step is gone.
- **Removed:** `tasks/deploy-intercept.yaml` (`deploy-stack-intercepts`),
  `build-images/Dockerfile.telepresence` (and the `telepresence` entry in
  `build-images/build-and-push.sh`), `scripts/install-telepresence-traffic-manager.sh`,
  `PR-TELEPRESENCE-INTERCEPT-CONFIRMATION.md`, the `deploy-intercepts-telepresence`
  branch in `pipeline/stack-pr-pipeline.yaml` and
  `pipeline/stack-pr-continue-pipeline.yaml` (`deploy-intercepts-mirrord` now
  runs unconditionally), and the Telepresence ServiceAccount block in
  `scripts/run-product-intercept-e2e.sh`.
- `intercept-backend` / `INTERCEPT_BACKEND` / Helm `interceptBackend` are kept
  for API compatibility; the only accepted value is `mirrord`.
- `tasks/deploy-intercept-mirrord.yaml`: proxy pod runs as `mirrord-intercept`
  (`scripts/install-mirrord-intercept-rbac.sh`, called by both runner scripts),
  `restartPolicy: Never`, fail-closed serving gate.
- `tasks/validate-propagation.yaml`: new `deployed-pods` param and the routing
  proof above.
- `scripts/run-product-intercept-e2e.sh`: `--tail=-1` on log collection so
  artifacts carry full step output.

## 6. Telepresence on a laptop (outside this repository)

If a developer prefers Telepresence to `mirrord exec` for local debugging, they
install it themselves per the Telepresence docs (traffic manager via the
`telepresence-oss` Helm chart) and run:

```bash
telepresence connect --namespace staging
telepresence intercept demo-fe --port 8080:80 --http-header x-dev-session=pr-42
# run demo-fe locally on :8080, attach a debugger, send a request with
# x-dev-session: pr-42 through the cluster entry point
telepresence leave demo-fe && telepresence quit
```

Nothing in the pipeline depends on it.

## 7. If anyone wants in-cluster Telepresence back

The history is in git (`git log -- tasks/deploy-intercept.yaml
build-images/Dockerfile.telepresence`). The last known blocker was small: the
client image lacked `iptables`, so the Telepresence root session exited at
connect time (section 3, last row). Any revival must run as its own
ServiceAccount, fail closed at deploy, and pass the routing proof in section 4
for both matched and unmatched traffic before a matrix entry is added.
