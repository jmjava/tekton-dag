# Orchestrator service

Flask service that runs in (or beside) the Kubernetes cluster: it receives **GitHub webhooks** and **manual API calls**, **resolves** which stack and app a repo maps to, **creates Tekton `PipelineRun`** objects via the Kubernetes API, and can **query Neo4j** for test-plan / graph helpers.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Liveness: returns `{"status":"ok"}`. |
| GET | `/readyz` | Readiness: confirms stack config loaded (`stacks_loaded` count). |
| GET | `/api/stacks` | List registered stacks from the resolver. |
| GET | `/api/teams` | List teams discovered from team config. |
| GET | `/api/runs` | Recent `PipelineRun` summary (`limit` query param, default 20). |
| POST | `/api/run` | Manual trigger: JSON body with `mode` `pr` \| `bootstrap` \| `merge` \| `promote` and fields per mode (see `routes.py`). |
| POST | `/api/bootstrap` | Trigger bootstrap pipeline (optional JSON `stack_file`). |
| POST | `/webhook/github` | GitHub `pull_request` webhook: HMAC-verified when secret configured; opens PR runs, merged close runs merge pipeline. |
| GET | `/api/apps/<app>/injection-status` | Secrets/ConfigMap injection plan and present/missing status (M13). |
| POST | `/api/reload` | Reload stack and team configs from disk. |
| GET | `/api/test-plan` | Neo4j test plan: query params `app` (required), `radius` (optional, default 1). |
| POST | `/api/graph/ingest` | Ingest traces or fixture file into Neo4j (see `routes.py`). |
| GET | `/api/graph/stats` | Graph node/edge statistics. |

## Environment variables

Defined in `app.py` (with defaults). Common ones:

| Variable | Purpose |
|----------|---------|
| `NAMESPACE` | Namespace for created `PipelineRun` resources. |
| `TEAM_NAME` | Team identifier (logging / config context). |
| `IMAGE_REGISTRY` | Container registry base passed into runs. |
| `CACHE_REPO` | Kaniko cache repository. |
| `INTERCEPT_BACKEND` | `telepresence` or `mirrord` (default `telepresence`). |
| `MAX_PARALLEL_BUILDS` | Parallelism hint (default `5`). |
| `GIT_URL` | Platform repo URL. |
| `GIT_REVISION` | Default branch/tag/SHA. |
| `STACK_FILE` | Default stack path in repo. |
| `STACKS_DIR` | Directory mounted with stack YAML (default `/stacks`). |
| `TEAMS_DIR` | Directory mounted with team YAML (default `/teams`). |
| `WEBHOOK_SECRET_NAME` | K8s Secret name holding the GitHub webhook HMAC secret (keys: `secret`, `value`, or `webhook-secret`). |
| `WEBHOOK_SECRET` | Optional direct HMAC secret (local/dev); preferred over fetching the K8s Secret when set. |
| `WEBHOOK_VERIFY_SIGNATURE` | When `true` (default) and a secret is available, require valid `X-Hub-Signature-256`. |
| `PIPELINE_TIMEOUT` | Default PipelineRun `spec.timeouts.pipeline` (default `2h`). |
| `MAX_RETRIES` | Default `max-retries` PipelineRun param (default `2`). |

Neo4j (used by graph endpoints) — see `graph_client.py`:

| Variable | Default |
|----------|---------|
| `NEO4J_URI` | `neo4j://graph-db:7687` |
| `NEO4J_USER` | `neo4j` |
| `NEO4J_PASSWORD` | `changeme` |

## Local development

```bash
cd orchestrator
python3 app.py
```

Listens on **0.0.0.0:8080** with Flask debug enabled when run as main.

## Testing

```bash
cd orchestrator
python3 -m pytest tests/ -v
```

## Docker

```bash
docker build -t orchestrator .
docker run -p 8080:8080 orchestrator
```

(Use the same env vars as in-cluster; mount kubeconfig or use in-cluster `ServiceAccount` when talking to the API.)

## Deployment

Enable the orchestrator in the Helm chart:

```yaml
orchestrationService:
  enabled: true
```

Set `orchestrationService.image` and related values in `helm/tekton-dag/values.yaml`. See **`../helm/tekton-dag/README.md`** for the full values table.
