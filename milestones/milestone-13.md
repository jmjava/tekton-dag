# Milestone 13 — Production Hardening

**Goal:** Make tekton-dag reliable and cost-effective on real infrastructure — spot instances, shared clusters, multi-environment promotion.

---

## 1. Retry on transient failures

Pipeline tasks that fail due to infrastructure problems — not test failures — should automatically retry.

- [ ] **Task-level retry policy** — add `retries: N` to build, deploy, and containerize tasks; leave test/validation tasks at `retries: 0` so real failures surface immediately
- [ ] **Spot instance preemption handling** — detect `node lost` / `pod evicted` / `DeadlineExceeded` exit codes and retry only those; distinguish from OOMKilled (which needs sizing, not retry)
- [ ] **Registry throttle / timeout retry** — Kaniko push and crane tag can hit rate limits or transient DNS failures; add retry with exponential backoff to `build-containerize` and `tag-release-images`
- [ ] **Configurable retry counts** — expose `max-retries` as a pipeline parameter so teams can tune per environment (e.g. 3 retries on spot, 0 on dedicated nodes)
- [ ] **Retry logging** — emit structured annotations on TaskRuns showing retry attempt number and original failure reason for post-mortem

## 2. Precise build image sizing

Build images currently use default resource requests. On shared clusters, this wastes capacity or causes OOMKill.

- [ ] **Per-tool resource profiles** — define CPU/memory requests and limits per build tool (Maven needs more heap than npm; Gradle benefits from more CPU for parallel compilation)
- [ ] **Helm-configurable sizing** — expose `resources.compile-maven`, `resources.compile-npm`, etc. in `values.yaml` so teams size to their workloads
- [ ] **Stack-level overrides** — allow `build.resources` in stack YAML per app (e.g. a large Spring Boot monolith needs 4Gi; a small Node service needs 512Mi)
- [ ] **Kaniko sizing** — separate resource profile for container build step; large multi-stage Dockerfiles need more memory than compile
- [ ] **LimitRange defaults** — document recommended `LimitRange` for the pipeline namespace so pods that don't specify limits get sane defaults
- [ ] **Monitoring baseline** — add a script or dashboard template that captures peak CPU/memory per TaskRun to inform sizing decisions

## 3. Multi-cluster push

Today tekton-dag builds and deploys within a single cluster. Production environments need images promoted to separate clusters.

- [ ] **Remote registry push** — after `tag-release-images`, optionally push released images to one or more remote registries (ECR, GCR, ACR, Harbor)
- [ ] **Registry list in config** — `stacks/registries.yaml` or Helm values: list of `{name, url, credentials-secret}` targets per environment (staging, production, DR)
- [ ] **Promotion pipeline** — new `stack-promote` pipeline: takes a release version + target environment, pulls from build registry, pushes to target, optionally triggers deployment (ArgoCD sync, Helm upgrade, Argo Rollouts)
- [ ] **Cross-cluster deploy task** — new Tekton task that applies manifests to a remote cluster using a kubeconfig secret (for non-GitOps setups)
- [ ] **Environment gates** — optional manual approval step between environments (e.g. staging → production requires a `/approve` comment or GUI button)
- [ ] **Promotion audit trail** — record which image was promoted to which environment, when, and by whom in Tekton Results

## 4. Operational reliability

- [ ] **Pipeline timeouts** — set explicit `timeout` on pipelines and critical tasks; today some tasks can hang indefinitely on a slow cluster
- [ ] **Graceful cleanup on timeout** — ensure `finally` block still runs when pipeline times out (intercept cleanup, PR comment with "timed out" status)
- [ ] **Health-check gates** — after deploy, wait for readiness probes before running tests (today deploy-full-stack doesn't confirm pods are Ready)
- [ ] **Results DB backup** — script to pg_dump Tekton Results Postgres on a schedule; document restore procedure
- [ ] **Neo4j persistence** — ensure graph data survives pod restarts (PVC + documented backup)

## 5. Observability

- [ ] **Pipeline metrics** — export Prometheus metrics: build duration per tool, test pass rate, retry count, queue time
- [ ] **Alerting rules** — sample Prometheus/Alertmanager rules: pipeline failure rate > threshold, build queue depth, registry push failures
- [ ] **Cost attribution** — label TaskRun pods with team/stack/app for cluster cost allocation tools (Kubecost, OpenCost)

## 6. Secrets injection

Today `deploy-full-stack` creates bare Deployments with only an image and port — no secrets, no env vars, no mounted config. Production apps need database credentials, API keys, and service tokens injected securely.

### Approach: External Secrets Operator + convention-based wiring

Use [External Secrets Operator (ESO)](https://external-secrets.io/) as the secrets provider. ESO syncs secrets from an external store (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, GCP Secret Manager) into native Kubernetes Secrets. The pipeline and deploy tasks wire those Secrets into app pods via `envFrom` and volume mounts using a naming convention tied to the stack YAML.

- [ ] **Stack YAML `secrets` block** — extend the app schema with an optional `secrets` section:
  ```yaml
  apps:
    - name: demo-bff
      secrets:
        env-from:          # injected as envFrom secretRef
          - demo-bff-db    # K8s Secret name (created by ESO or manually)
          - demo-bff-api-keys
        volume-mounts:     # mounted as files (TLS certs, service account keys)
          - secret: demo-bff-tls
            mount-path: /etc/tls
  ```
- [ ] **Schema validation** — update `stacks/schema.json` to validate the `secrets` block: `env-from` is an array of strings (Secret names); `volume-mounts` is an array of `{secret, mount-path}` objects
- [ ] **Deploy task wiring** — update `deploy-full-stack` to read each app's `secrets` block from the resolved stack JSON and add `envFrom[].secretRef` and `volumeMounts` + `volumes` to the generated Deployment spec
- [ ] **Intercept deploy wiring** — update `deploy-intercept` and `deploy-intercept-mirrord` to inject the same secrets into PR pods so intercepted traffic has valid credentials
- [ ] **Convention-based naming** — document the naming convention: `<app-name>-<purpose>` (e.g. `demo-bff-db`, `demo-fe-oauth`). Teams create Secrets manually or via ESO ExternalSecret CRs in their namespace
- [ ] **ESO SecretStore per team** — Helm template for a `ClusterSecretStore` or per-namespace `SecretStore` that connects to the team's secret backend; document setup for AWS Secrets Manager, Vault, and Azure Key Vault
- [ ] **ExternalSecret templates** — provide example `ExternalSecret` CRs that sync from the external store into the K8s Secrets referenced in the stack YAML; include in `helm/tekton-dag/templates/` as optional resources gated by `secrets.externalSecretsEnabled`
- [ ] **Sealed Secrets fallback** — for clusters without an external secret store, document using [Sealed Secrets](https://sealed-secrets.netlify.app/) to encrypt secrets into Git-safe `SealedSecret` CRs that the controller decrypts at deploy time
- [ ] **Pipeline secret validation** — add a pre-deploy check in `deploy-full-stack` that verifies all referenced K8s Secrets exist before creating Deployments; fail fast with a clear message if a Secret is missing rather than letting pods crash-loop
- [ ] **Management GUI integration** — surface secret status (present / missing / last-synced) on the app detail panel in the Management GUI, reading from ESO `ExternalSecret` status conditions

## 7. Per-app configuration per environment

Apps need different configuration across environments (local, staging, production) — database URLs, feature flags, log levels, external service endpoints. This should not be baked into container images.

### Approach: ConfigMap layering via stack YAML + Helm values

Each app gets a ConfigMap per environment, injected as env vars or mounted files. The stack YAML declares what config an app needs; Helm values provide environment-specific values.

- [ ] **Stack YAML `config` block** — extend the app schema with an optional `config` section:
  ```yaml
  apps:
    - name: demo-bff
      config:
        env-from:             # injected as envFrom configMapRef
          - demo-bff-config   # K8s ConfigMap name
        volume-mounts:        # mounted as files
          - configmap: demo-bff-properties
            mount-path: /etc/config
  ```
- [ ] **Schema validation** — update `stacks/schema.json` to validate the `config` block, mirroring the `secrets` structure but for ConfigMaps
- [ ] **Deploy task wiring** — update `deploy-full-stack` to inject `envFrom[].configMapRef` and ConfigMap `volumeMounts` into generated Deployments from the app's `config` block
- [ ] **Intercept deploy wiring** — apply same ConfigMaps to PR pods so intercepted services behave identically
- [ ] **Helm ConfigMap templates** — generate per-app ConfigMaps from Helm values, allowing teams to define env-specific config in `values.yaml`:
  ```yaml
  appConfig:
    demo-bff:
      DATABASE_URL: "postgresql://localhost:5432/bff"
      LOG_LEVEL: "info"
      FEATURE_NEW_UI: "false"
    demo-fe:
      API_BASE_URL: "http://demo-bff:8080"
  ```
  The Helm template iterates `appConfig` and creates a ConfigMap per app (`demo-bff-config`, `demo-fe-config`), automatically matching the stack YAML `env-from` references
- [ ] **Environment overlay pattern** — document how teams maintain separate values files per environment (`values-local.yaml`, `values-staging.yaml`, `values-prod.yaml`) with different `appConfig` entries; `helm upgrade -f values-staging.yaml` applies the right config
- [ ] **Config validation hook** — optional `pre-deploy` hook task that checks ConfigMaps exist and contain required keys (defined in a `config-schema` section in stack YAML); fail fast if config is missing
- [ ] **`.env` file support for local dev** — `generate-run.sh` reads a `.env.<app>` file and creates a ConfigMap from it before triggering the pipeline, matching the config block in stack YAML so local dev mirrors cluster behavior
- [ ] **Management GUI config view** — add a config panel in the app detail view showing current ConfigMap contents (masked for secrets), last-modified timestamp, and environment source

---

## Segment 18 — What's Coming Next

A demo video (segment 18) presents the first 5 pillars of production hardening as a roadmap walkthrough, showing the problems each solves and the planned approach. Pillars 6 (secrets) and 7 (per-app config) were added after the initial recording and will be covered in a future update.
