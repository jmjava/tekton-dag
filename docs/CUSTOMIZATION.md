# Customizing tekton-dag

Practical recipes for extending teams, stacks, build images, registries, pipelines, and intercept behavior. Examples use paths from the main **tekton-dag** platform repository.

**New team or new stack from scratch?** See [TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md](TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md) for which **baggage / header-forwarding library** to use per language and an end-to-end **stack creation checklist** (YAML, Helm, orchestrator).

---

## 1. Add a new team

**Goal:** Isolate config, labels, and orchestrator defaults for another group.

1. **Repository layout** — add `teams/<team>/team.yaml` and `teams/<team>/values.yaml`:

`teams/squad-b/team.yaml` (orchestrator and docs; loaded from `/teams` when packaged):

```yaml
name: squad-b
namespace: tekton-pipelines
cluster: prod-us-east
imageRegistry: registry.internal/squad-b
cacheRepo: registry.internal/squad-b/kaniko-cache
interceptBackend: telepresence
maxConcurrentRuns: 5
maxParallelBuilds: 8
stacks:
  - stacks/squad-b-core.yaml
```

`teams/squad-b/values.yaml` (Helm overrides for that release):

```yaml
teamName: "squad-b"
namespace: "tekton-pipelines"
imageRegistry: "registry.internal/squad-b"
cacheRepo: "registry.internal/squad-b/kaniko-cache"
interceptBackend: "telepresence"
maxParallelBuilds: 8
stackFile: "stacks/squad-b-core.yaml"
gitUrl: "https://github.com/myorg/platform.git"
gitRevision: "main"
orchestrationService:
  enabled: true
  image: "registry.internal/squad-b/tekton-dag-orchestrator:latest"
```

2. **Helm chart** — run `helm/tekton-dag/package.sh`, then copy team YAML into the chart’s raw path so `configmap-teams.yaml` renders:

```bash
mkdir -p helm/tekton-dag/raw/teams/squad-b
cp teams/squad-b/team.yaml helm/tekton-dag/raw/teams/squad-b/
```

3. **Stacks** — add `stacks/squad-b-core.yaml` and ensure `package.sh` copies it into `raw/stacks/`.

4. **Deploy** — `helm upgrade --install tekton-dag-squad-b ./helm/tekton-dag -n tekton-pipelines -f teams/squad-b/values.yaml`.

---

## 2. Add an app to a stack

**Goal:** Register another service in the DAG (build, image, tests, downstream edges).  
**Baggage:** add the matching library from `libs/` and set `propagation-role`—see [TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md](TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md).

Edit or create a stack file under `stacks/`. Each entry under `apps` needs a unique `name`, `repo`, `role`, `build` tool settings, and optional `downstream` / `tests`:

```yaml
# stacks/my-stack.yaml (excerpt)
name: my-stack
defaults:
  namespace: staging
  image-registry: "${IMAGE_REGISTRY}"

apps:
  - name: new-api
    repo: myorg/new-api
    role: persistence
    propagation-role: terminal
    context-dir: "."
    dockerfile: Dockerfile
    build:
      tool: maven
      runtime: spring-boot
      java-version: "21"
      build-command: "mvn -B clean package -DskipTests"
    downstream: []
    tests:
      postman: tests/postman/api.json
```

`tool` must match a compile path your pipelines support (`npm`, `maven`, `gradle`, `pip`, `composer` / PHP flows). After changing stacks, run `helm/tekton-dag/package.sh` before upgrading the chart so the stacks ConfigMap updates.

---

## 3. Add a new build tool variant

**Goal:** Support another language runtime tag (e.g. Java 25) end-to-end.

1. **Dockerfile** — add or extend build args in `build-images/Dockerfile.<tool>` (example pattern from Maven):

```dockerfile
ARG JAVA_VERSION=21
FROM maven:3.9-eclipse-temurin-${JAVA_VERSION}
# ...
```

2. **Build matrix** — extend `VARIANT_MAP` in `build-images/build-and-push.sh` and run:

```bash
cd build-images
REGISTRY=my.registry.io ./build-and-push.sh --matrix --tool maven
```

3. **Helm values** — add a matching entry under `compileImageVariants` in `helm/tekton-dag/values.yaml`:

```yaml
compileImageVariants:
  maven-java25: "my.registry.io/tekton-dag-build-maven:java25"
```

4. **PipelineRuns** — pass the corresponding `compile-image-maven` (or other tool) param so the compile Task uses that image (`scripts/generate-run.sh` with `--build-images` builds defaults from `IMAGE_REGISTRY`).

---

## 4. Change the container registry

**Goal:** Point Kaniko, app images, and compile images at a new registry.

1. **Helm** — set `imageRegistry`, `cacheRepo`, `compileImages`, `compileImageVariants`, and `orchestrationService.image` in `values.yaml` or a team override file.

2. **Scripts / local env** — `scripts/common.sh` defaults `IMAGE_REGISTRY` to `localhost:5001`; override with environment or a repo `.env`:

```bash
export IMAGE_REGISTRY=my.registry.io:443
./scripts/publish-build-images.sh   # uses load_env + REGISTRY
```

`publish-build-images.sh` calls `build-images/build-and-push.sh`, which honors `REGISTRY` and positional args. For Kind, `resolve_compile_registry` maps `localhost:5001` → `localhost:5000` for in-cluster references.

---

## 5. Override pipeline defaults per team

**Goal:** Different defaults per team without editing shared pipeline YAML.

| Mechanism | What it controls |
|-----------|------------------|
| **Helm values per release** | Orchestrator env: `INTERCEPT_BACKEND`, `STACK_FILE`, `GIT_*`, `IMAGE_REGISTRY`, `CACHE_REPO`, `MAX_PARALLEL_BUILDS`. |
| **`POST /api/run`** | JSON body may include `intercept_backend`, `stack_file`, `git_revision` for one-off overrides. |
| **PipelineRun params** | `generate-run.sh` flags (`--intercept-backend`, `--registry`, …) map directly to pipeline parameters. |
| **`team.yaml`** | Documents team limits, stacks, and registry; keep in sync with Helm for clarity. `/api/teams` exposes this file. |

Example manual API call:

```json
POST /api/run
{
  "mode": "pr",
  "changed_app": "demo-fe",
  "pr_number": 99,
  "intercept_backend": "mirrord",
  "stack_file": "stacks/stack-two-vendor.yaml"
}
```

---

## 6. Add a custom hook task

**Goal:** Run extra logic after clone, after image build, around tests, or in `finally`.

1. **Define a Task** in `tasks/` (see `tasks/examples/example-image-scan.yaml` for `post-build`, `example-slack-notify.yaml` for `post-test`):

```yaml
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: my-pre-build
  labels:
    tekton-dag/hook-type: "pre-build"
spec:
  steps:
    - name: run
      image: alpine:3.20
      script: |
        #!/bin/sh
        set -e
        echo "Custom pre-build"
```

2. **Apply** the Task to the pipeline namespace (`kubectl apply -f tasks/my-pre-build.yaml -n tekton-pipelines` or include it in chart packaging).

3. **Pass the Task name** as a pipeline parameter (`pre-build-task`, `post-build-task`, `pre-test-task`, or `post-test-task`). Empty string skips the hook. Pipelines use a `WhenExpression` on the param so missing Tasks are not required until you set the name.

---

## 7. Change language versions for an app

**Goal:** Pin Node, Java, Python, or PHP for a specific service.

Set fields under `build` in the stack YAML; they are preserved in resolved stack JSON for tooling and documentation:

```yaml
build:
  tool: npm
  runtime: vue
  node-version: "20"
  build-command: "npm ci && npm run build"
```

```yaml
build:
  tool: maven
  java-version: "17"
  build-command: "mvn -B clean package -DskipTests"
```

```yaml
build:
  tool: pip
  python-version: "3.11"
  build-command: "pip install -r requirements.txt && pytest -q"
```

```yaml
build:
  tool: composer
  php-version: "8.2"
  build-command: "composer install --no-dev --optimize-autoloader"
```

Ensure a **compile image** exists that matches that toolchain (build and push with `build-and-push.sh --matrix`, then set `compileImageVariants` and pass the right `compile-image-*` on the PipelineRun). For a PR run that builds only one app, a single `compile-image-maven` value matching that app’s Java version is enough.

---

## 8. Add intercept backend support

**Goal:** Use **mirrord** instead of **Telepresence** (or switch per environment).

1. **Cluster** — install the components your chosen backend needs (e.g. Telepresence Traffic Manager or mirrord operator per vendor docs).

2. **Helm** — set `interceptBackend: "mirrord"` in values; the orchestrator sets `INTERCEPT_BACKEND` for webhook-created runs.

3. **Pipeline param** — `stack-pr-test` already exposes `intercept-backend` (`telepresence` | `mirrord`). `generate-run.sh` supports:

```bash
./scripts/generate-run.sh --mode pr --repo demo-fe --pr 1 --intercept-backend mirrord --apply
```

4. **Images** — ensure `compileImages.mirrord` points to a pushed `tekton-dag-build-mirrord` image when mirrord tasks run.

5. **Manual API** — `POST /api/run` accepts `"intercept_backend": "mirrord"` for PR mode.

For details on mirrord tasks and scenarios, see [m7-mirrord-intercept-task.md](./m7-mirrord-intercept-task.md) in this docs folder.
