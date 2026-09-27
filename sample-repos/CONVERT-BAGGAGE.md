# Convert sample apps to the baggage contract

Sample apps must **echo the original override** and **call `install()` / add the starter**. The pipeline’s `validate-stack-propagation` task is **fail-closed**: a missing or rewritten `pr-42` fails the run.

## Hop-report shape

Backends should serve `GET /propagation` (and may use the same body for `/`):

```json
{
  "app": "release-lifecycle-demo",
  "session": "pr-42",
  "hops": [
    { "app": "demo-api", "session": "pr-42", "hops": [] }
  ]
}
```

`session` is the value `install()` adopted — never a newly minted substitute. Optional `DOWNSTREAM_URL` (or `BFF_UPSTREAM` on the Vue nginx proxy) nests the next hop.

Set `APP_NAME` to the **stack app name** (`demo-fe`, `release-lifecycle-demo`, …). The validator also accepts the GitHub repo basename (`tekton-dag-vue-fe`) as an alias.

A static Vue originator cannot read request headers in JS. The conversion nginx config:

1. Proxies `/propagation` to the BFF **with the incoming headers intact**.
2. Sets a `x-dev-session` cookie so `install()` can attach the same value on browser `fetch`.

## Apply locally

```bash
# clones already in /path/to/sample-apps/{tekton-dag-vue-fe,...}
./sample-repos/apply-baggage-conversion.sh /path/to/sample-apps

# emit env that matches stacks/stack-one.yaml
./scripts/emit-baggage-env.sh --stack stacks/stack-one.yaml --all
./scripts/baggage-doctor.sh --stack stacks/stack-one.yaml
```

Then commit and push **each** sample repo. This platform PR cannot open those GitHub PRs.

## Per repo

| Repo | Incoming | Outgoing | Echo |
|------|----------|----------|------|
| tekton-dag-vue-fe | nginx cookie + query; `install()` | patched `fetch` | nginx proxies `/propagation` |
| tekton-dag-spring-boot | starter filter (baggage profile) | RestTemplate interceptor | JSON `/` and `/propagation` |
| tekton-dag-spring-boot-gradle | keep filter until starter is a dep | add starter; do not hand-copy | JSON + request attribute |
| tekton-dag-spring-legacy | `BaggageServletFilter` in `web.xml` | `BaggageOutgoing.apply` | JSON servlet |
| tekton-dag-flask | `install(app)` | instrumented `requests` | JSON `/` and `/propagation` |
| tekton-dag-php | `Baggage::install()` | `Baggage::guzzleClient()` | JSON `public/index.php` |

Libraries default **off**. `deploy-full-stack` and the intercept tasks inject `BAGGAGE_*`, `APP_NAME`, and `DOWNSTREAM_URL` / `BFF_UPSTREAM` from the stack. Local/Vite still needs `emit --format vite` at image build time. Set `propagation.enabled: false` to skip injection.
