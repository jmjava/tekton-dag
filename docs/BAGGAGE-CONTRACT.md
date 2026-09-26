# Baggage contract: transfer the original override header

A PR (or other override) deploys **one container somewhere in the stack**. Intercepts route only the traffic that carries that run’s session, usually `x-dev-session: pr-42`.

**The original value must be transferred unchanged from call to call.** If hop 2 drops it or replaces it, the override container at hop 3 never sees the match and baseline traffic is what you test.

Machine-readable spec and fixtures: [`libs/baggage-contract/`](../libs/baggage-contract/). Reference implementation: [`tekton_dag_common.baggage_contract`](../libs/tekton-dag-common/tekton_dag_common/baggage_contract.py).

```
client  --x-dev-session: pr-42-->  originator  --pr-42-->  forwarder  --pr-42-->  terminal
                                      FE                     BFF                    API
```

If `demo-api` is the PR pod, Telepresence/mirrord match `pr-42` on the API service. The FE and BFF do not invent a new session. They copy `pr-42`.

## Rules (every language)

| Role | Incoming | Outgoing |
|------|----------|----------|
| **Originator** | **Adopt** header, then cookie, then query. Mint `sessionValue` only if nothing arrived (local debug). | Attach that same value + W3C `baggage` |
| **Forwarder** | Adopt incoming only. Never mint. | Copy that exact value |
| **Terminal** | Adopt incoming (for intercept match / logs). | Never forward |
| **Unknown / disabled** | Fail closed: do nothing | Do nothing |

Invariant: a present incoming override **wins over** any configured mint value. Clients must not rewrite `pr-42` to something else.

## What an app team does

Do **not** write header-copying code.

1. Add the library for the runtime.
2. Call `install()` (Spring Boot: add the starter).
3. Emit env from the stack so header name and role match YAML:

```bash
python -m tekton_dag_common.baggage_contract emit --stack stacks/stack-one.yaml --app demo-fe --format vite
./scripts/baggage-doctor.sh --stack stacks/stack-one.yaml
```

| Runtime | Incoming | Outgoing (automatic) |
|---------|----------|----------------------|
| Spring Boot | Filter | `RestTemplate` interceptor + `BaggagePropagator.apply` |
| Servlet / WAR | Filter | `BaggageOutgoing.apply` |
| Flask | `install(app)` | `requests.Session` is instrumented |
| Node / Vue | `adoptIncoming` / query+cookie | `install()` patches `fetch` |
| PHP | `Baggage::install()` | `Baggage::guzzleClient()` |

## Production safety

`BAGGAGE_ENABLED` / `baggage.enabled` / `VITE_BAGGAGE_ENABLED` default **off**. Production builds omit the library or leave it disabled.

## Hop-report (fail-closed validation)

`validate-stack-propagation` sends the original header to the originator and **exits 1** if any required hop dropped or rewrote it. Apps should echo:

```json
{
  "app": "demo-fe",
  "session": "pr-42",
  "hops": [
    {
      "app": "release-lifecycle-demo",
      "session": "pr-42",
      "hops": [{ "app": "demo-api", "session": "pr-42" }]
    }
  ]
}
```

Serve this on `GET /propagation` (optional alias: `/`). A static frontend proxies `/propagation` to the BFF and sets a cookie so `install()` can attach the same value on browser `fetch`.

```bash
python -m tekton_dag_common.propagation_validate evaluate \
  --chain "demo-fe release-lifecycle-demo demo-api" \
  --header-val pr-42 --build-apps demo-api --response -
python -m tekton_dag_common.propagation_validate simulate \
  --stack stacks/stack-one.yaml --header-val pr-42
```

Sample-app conversion kit: [`sample-repos/CONVERT-BAGGAGE.md`](../sample-repos/CONVERT-BAGGAGE.md).

## Conformance

Shared vectors in [`libs/baggage-contract/vectors.json`](../libs/baggage-contract/vectors.json) are loaded by Python, Node, and PHP tests. Java modules assert the same cases. `scripts/run-baggage-conformance.sh` runs the suite.
