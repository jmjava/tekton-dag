# tekton-dag Helm chart

Tekton-based CI/CD for multi-app stacks: stack resolution, Kaniko builds, PR intercept testing (Telepresence or mirrord), and an optional in-cluster orchestration service (GitHub webhooks, manual runs).

## Prerequisites

- **Kubernetes** cluster with **Tekton Pipelines** installed (same major version your tasks/pipelines target).
- Namespace for Tekton (default in values: `tekton-pipelines`).
- For the orchestrator: **Secrets** referenced by values (`triggers.webhookSecretName`, `triggers.githubTokenSecretName`) when using webhooks / PR comments.
- **Git SSH**: pipeline workspaces expect clone secrets (e.g. `ssh-key-secret`) consistent with your cluster bootstrap.
- Before `helm template` / `helm install`, run **`./package.sh`** from this chart directory so `raw/tasks`, `raw/pipelines`, and `raw/stacks` are populated from the repository root.

## Quick install

From the repository root:

```bash
cd helm/tekton-dag
./package.sh
# Optional: stage team configs for ConfigMaps (orchestrator reads /teams/<team>/team.yaml)
mkdir -p raw/teams/default
cp ../../teams/default/team.yaml raw/teams/default/

helm upgrade --install tekton-dag . \
  --namespace tekton-pipelines \
  --create-namespace \
  -f values.yaml
```

Use `-f` with a per-team values file (for example `teams/<team>/values.yaml`) when deploying multiple releases.

## Chart layout

| Path | Purpose |
|------|---------|
| `templates/_helpers.tpl` | Labels, names, service account helper |
| `templates/orchestration-deployment.yaml` | Orchestrator Deployment + Service (optional) |
| `templates/rbac.yaml` | ServiceAccount and optional cluster-admin binding |
| `templates/pipelines/pipelines.yaml` | Tekton pipelines/triggers from packaged `raw/pipelines/*.yaml` |
| `templates/tasks/tasks.yaml` | Tekton tasks from packaged `raw/tasks/*.yaml` |
| `templates/configmap-stacks.yaml` | `tekton-dag-stacks`: all `raw/stacks/*.yaml` |
| `templates/configmap-teams.yaml` | One ConfigMap per `raw/teams/<team>/team.yaml` (`tekton-dag-teams-<team>`) |
| `templates/pvc-build-cache.yaml` | Optional PVC for Kaniko/build cache workspace |

Packaged content under `raw/` is **not** committed by default; `package.sh` copies from `tasks/`, `pipeline/`, and `stacks/` at the repo root. Copy team files into `raw/teams/` yourself if you use team ConfigMaps.

## Configuration reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `teamName` | string | `"default"` | Team label (`tekton-dag/team`) and Helm fullname prefix |
| `namespace` | string | `"tekton-pipelines"` | Target namespace for chart resources |
| `imageRegistry` | string | `"localhost:5000"` | Container registry base for runtime images; passed to orchestrator as `IMAGE_REGISTRY` |
| `buildImageTag` | string | `"latest"` | Tag convention for build images (document alongside `compileImages`) |
| `cacheRepo` | string | `"localhost:5000/kaniko-cache"` | Kaniko cache repository; passed to orchestrator as `CACHE_REPO` |
| `interceptBackend` | string | `"telepresence"` | Default intercept backend: `telepresence` or `mirrord` (`INTERCEPT_BACKEND` env) |
| `maxParallelBuilds` | int | `5` | Max concurrent Kaniko-style builds for bootstrap-style runs (`MAX_PARALLEL_BUILDS` env) |
| `compileImages.npm` | string | see `values.yaml` | Default compile image for npm |
| `compileImages.maven` | string | … | Default compile image for Maven |
| `compileImages.gradle` | string | … | Default compile image for Gradle |
| `compileImages.pip` | string | … | Default compile image for pip/Python |
| `compileImages.php` | string | … | Default compile image for PHP/Composer |
| `compileImages.mirrord` | string | … | Image for mirrord proxy workloads |
| `compileImageVariants` | map | see `values.yaml` | Keys `maven-java17`, `npm-node20`, etc. → full image refs; mirror tags from `build-images/build-and-push.sh --matrix` |
| `gitUrl` | string | … | Platform repo URL for orchestrator (`GIT_URL`) |
| `gitRevision` | string | `"main"` | Platform repo revision (`GIT_REVISION`) |
| `stackFile` | string | `"stacks/stack-one.yaml"` | Default stack path for orchestrator (`STACK_FILE`) |
| `rbac.create` | bool | `true` | Create ServiceAccount |
| `rbac.serviceAccountName` | string | `"tekton-pr-sa"` | Service account name for pipelines and orchestrator |
| `rbac.clusterAdmin` | bool | `true` | Bind SA to `cluster-admin` (tighten for production) |
| `workspaces.sharedWorkspace.storageClass` | string | `""` | Storage class for shared PVCs created by PipelineRuns (if you use volumeClaimTemplate externally) |
| `workspaces.sharedWorkspace.size` | string | `"2Gi"` | Documented default size for shared workspace |
| `workspaces.buildCache.enabled` | bool | `true` | Whether pipelines expect a `build-cache` workspace |
| `workspaces.buildCache.create` | bool | `false` | Chart creates a PVC named `build-cache` when `true` |
| `workspaces.buildCache.storageClass` | string | `""` | Storage class for chart-created build-cache PVC |
| `workspaces.buildCache.size` | string | `"5Gi"` | Size for chart-created build-cache PVC |
| `orchestrationService.enabled` | bool | `true` | Deploy orchestrator Deployment/Service |
| `orchestrationService.image` | string | … | Orchestrator container image |
| `orchestrationService.replicas` | int | `1` | Replica count |
| `orchestrationService.port` | int | `8080` | Container and Service port |
| `orchestrationService.resources` | object | requests/limits | Pod resources |
| `triggers.enabled` | bool | `true` | Included for parity with values; trigger YAML is shipped under `raw/pipelines/` |
| `triggers.webhookSecretName` | string | `"github-webhook-secret"` | Secret for GitHub HMAC (orchestrator env) |
| `triggers.githubTokenSecretName` | string | `"github-token"` | Secret name for PR comment token (pipelines) |
| `dashboard.url` | string | `""` | Optional Tekton Dashboard base URL for PR links |

`compileImages` / `compileImageVariants` are the **source of truth** for image URLs you pass into PipelineRuns as `compile-image-*` parameters (see `scripts/generate-run.sh`). Wiring those params from Helm into every trigger is cluster-specific; keep values aligned with the images you push.

## Multi-team setup

Typical pattern: **one Helm release per team** (often via Argo CD ApplicationSet), each with:

- Its own `teamName` and `namespace` (or cluster).
- Its own `values.yaml` (see `teams/<team>/values.yaml` in the repo).
- Stack YAML checked into `stacks/` and copied into `raw/stacks/` via `package.sh`.
- Optional `raw/teams/<team>/team.yaml` so the chart emits `tekton-dag-teams-<team>`; the orchestrator discovers team files under `/teams/<team>/team.yaml`.

The orchestrator resolves **repo → stack → app** from stack YAML loaded from the stacks ConfigMap. `team.yaml` lists stacks and team-level defaults (registry, cache, intercept backend, limits) for documentation and for `/api/teams`; keep Helm env vars and team files consistent for a given cluster.

The resolver expects files at `/teams/<team>/team.yaml`. The chart template emits one ConfigMap per `raw/teams/<team>/team.yaml` (`tekton-dag-teams-<team>`). If you use multiple teams, align the orchestrator Deployment’s `teams` volume with that layout (for example a projected volume or a single aggregated ConfigMap) so those paths exist inside the pod.

## Build variant images

Version-specific images use tags such as `java17`, `node20`, `python312`, `php83`. Build them with:

```bash
cd build-images
./build-and-push.sh --matrix                    # all tools
./build-and-push.sh --matrix --tool maven       # one tool
```

Each Dockerfile accepts build args (e.g. `JAVA_VERSION`, `NODE_VERSION`); see comments in `Dockerfile.maven`, `Dockerfile.node`, etc. Mirror the printed image references into `compileImageVariants` in `values.yaml`.

## Custom hook tasks

Pipelines expose optional parameters: `pre-build-task`, `post-build-task`, `pre-test-task`, `post-test-task`. When non-empty, the pipeline runs the referenced **Tekton Task name** at the documented stage.

Examples live under `tasks/examples/` (annotate tasks with `tekton-dag/hook-type` for clarity). Deploy the Task in the same namespace as the pipeline, then pass the Task’s `metadata.name` as the parameter value (via TriggerTemplate, `generate-run.sh`, or extended orchestrator).

## Upgrading

1. Pull the new chart sources and run `./package.sh` to refresh `raw/`.
2. Review `values.yaml` for new keys and merge into your override files.
3. Run `helm diff upgrade` (if installed) then `helm upgrade`.
4. If Tekton CRDs or API versions changed, upgrade Tekton on the cluster first, then apply chart changes.
5. Rebuild and push build images if Dockerfiles or variant matrix changed.

## Example: override values for a specific team

`teams/acme/values.yaml`:

```yaml
teamName: "acme"
namespace: "tekton-pipelines-acme"
imageRegistry: "123456789012.dkr.ecr.us-west-2.amazonaws.com"
cacheRepo: "123456789012.dkr.ecr.us-west-2.amazonaws.com/acme/kaniko-cache"
interceptBackend: "mirrord"
maxParallelBuilds: 8

gitUrl: "https://github.com/acme/platform.git"
gitRevision: "main"
stackFile: "stacks/acme-main.yaml"

compileImages:
  npm: "123456789012.dkr.ecr.us-west-2.amazonaws.com/tekton-dag-build-node:v2025.03.1"
  maven: "123456789012.dkr.ecr.us-west-2.amazonaws.com/tekton-dag-build-maven:v2025.03.1"
  # ...gradle, pip, php, mirrord

orchestrationService:
  enabled: true
  image: "123456789012.dkr.ecr.us-west-2.amazonaws.com/tekton-dag-orchestrator:v2025.03.1"
  replicas: 2
  resources:
    requests:
      cpu: "200m"
      memory: "256Mi"
    limits:
      cpu: "1"
      memory: "512Mi"

rbac:
  clusterAdmin: false   # prefer a dedicated Role/RoleBinding in production
```

Install:

```bash
helm upgrade --install tekton-dag-acme ./helm/tekton-dag \
  -n tekton-pipelines-acme --create-namespace \
  -f teams/acme/values.yaml
```

## Optional chart values

`nameOverride` (string) can be set to shorten generated resource names; see `templates/_helpers.tpl`.
