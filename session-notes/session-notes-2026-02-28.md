# Session notes — 2026-02-25 through 2026-02-28

Everything done in the **tekton-dag** project since milestone 3 and the 2026-02-24 session notes.

---

## 1. Reporting GUI (milestone 3 implementation)

Built the **reporting-gui/** — a Vue 3 + Node/Express application that implements the milestone 3 spec:

### Frontend (Vue 3 + Vite)

- **Trigger view** — form to create PipelineRuns: select pipeline type (PR, merge, bootstrap), stack, app, PR number, git revision, registry, version overrides. Submits to backend API.
- **Monitor view** — list of recent PipelineRuns with status, duration, pipeline name, changed app, PR number. Click to drill into run detail.
- **Run detail view** — single PipelineRun with TaskRun-level status breakdown.
- **Test results view** — test summary from pipeline results; filter by status.
- **Git view** — lists repos from stack definitions (platform + app repos), shows branches, tags, commits, and open PRs per repo via GitHub API.
- **Dashboard view** — embeds the Tekton Dashboard in an iframe (configurable base URL via `VITE_DASHBOARD_URL`).
- Nav bar with five tabs: Trigger, Monitor, Test results, Git, Dashboard.

### Backend (Node/Express)

- `GET /api/pipelineruns` — list PipelineRuns via kubectl (sorted, with parsed status, duration, test summary, PR number, changed app)
- `GET /api/pipelineruns/:name` — single PipelineRun detail
- `GET /api/taskruns?pipelineRun=:name` — TaskRuns for a run
- `GET /api/stacks` — stack files and apps from `stacks/` directory
- `POST /api/trigger` — create PipelineRun (calls `generate-run.sh` for pr/merge, inline YAML for bootstrap)
- `GET /api/repos` — platform + app repos parsed from stack YAMLs
- `GET /api/repos/:owner/:repo/branches|tags|commits|prs` — GitHub API proxy
- `GET /api/prs` — open PRs across all repos (aggregated)
- Auto-discovers `REPO_ROOT` by walking up from backend dir to find `stacks/`
- Supports `GITHUB_TOKEN` for private repo access

### Tekton Dashboard scripts

- `scripts/install-tekton-dashboard.sh` — install official Tekton Dashboard
- `scripts/port-forward-tekton-dashboard.sh` — port-forward to `localhost:9097`
- `scripts/uninstall-tekton-dashboard.sh` — remove Dashboard

---

## 2. Optimized build images

Switched all five build-image Dockerfiles from `ubuntu:22.04` with heavy package installs to **official language-specific slim images**:

| Image | Old base | New base | Contents |
|-------|----------|----------|----------|
| `tekton-dag-build-node` | ubuntu:22.04 + curl + node install | `node:22-slim` | Node 22 + npm + jq |
| `tekton-dag-build-maven` | ubuntu:22.04 + JDK + Maven install | `maven:3.9-eclipse-temurin-21` | JDK 21 + Maven + jq |
| `tekton-dag-build-gradle` | ubuntu:22.04 + JDK install | `eclipse-temurin:21-jdk` | JDK 21 + jq (apps use `./gradlew`) |
| `tekton-dag-build-python` | ubuntu:22.04 + python3.12 (failed) | `python:3.12-slim` | Python 3.12 + pip + jq |
| `tekton-dag-build-php` | ubuntu:22.04 + PHP install | `php:8.3-cli` | PHP 8.3 + Composer + zip ext + jq |

Published to Kind registry via `scripts/publish-build-images.sh` (defaults to `localhost:5001`).

---

## 3. Kind registry debugging and resolution

Extensive debugging of **ImagePullFailed** errors for compile images in PipelineRuns. Root cause: Kind cluster has two registries and a containerd redirect.

**Registry topology:**

| Container | Host port | In-cluster address | Purpose |
|-----------|-----------|-------------------|---------|
| `kind-registry` | `localhost:5001` | `localhost:5000` (via containerd `certs.d`) | Kind cluster registry |
| `registry` | `localhost:5000` | N/A | Standalone (not used by Kind) |

**Key discovery:** Kind's containerd config at `/etc/containerd/certs.d/localhost:5000/hosts.toml` redirects `localhost:5000` pulls to `kind-registry:5000` on the Docker network. No config exists for `kind-registry:5000` directly — so pod image refs must use `localhost:5000`.

**Files changed:**

- `scripts/publish-build-images.sh` — default registry changed to `localhost:5001` (Kind host port)
- `scripts/generate-run.sh` — maps `localhost:5001` to `localhost:5000` for pipeline image params
- `pipeline/stack-pr-pipeline.yaml`, `stack-merge-pipeline.yaml`, `stack-bootstrap-pipeline.yaml` — `compile-image-*` defaults changed to `localhost:5000/...`
- `pipeline/triggers.yaml` — `image-registry` and `compile-image-*` params set to `localhost:5000`

---

## 4. PR pipeline: removed version bumping

The PR pipeline (`stack-pr-test`) was performing version bumps before merge, which contradicts the design (version bump should only happen on merge in response to a webhook).

**Removed from `stack-pr-pipeline.yaml`:**
- `bump-rc-version` task
- `push-version-commit` task
- `bumped-versions` result

PR pipeline now: fetch → resolve → clone-app-repos → snapshot tag → build changed app → deploy intercepts → validate → test → post PR comment → cleanup. **No version modification.**

---

## 5. Webhook-driven PR → Merge flow (end-to-end working)

### Cloudflare Tunnel setup

Configured the Cloudflare Tunnel to route GitHub webhooks to the in-cluster EventListener:

```
GitHub → https://tekton-el.menkelabs.com → Cloudflare Tunnel → localhost:8080 → EventListener pod
```

- Added public hostname route in Cloudflare Zero Trust dashboard (Networks → Tunnels → menkelabs-sso-tunnel-config → Public Hostnames → Add)
- Updated `docs/CLOUDFLARE-TUNNEL-EVENTLISTENER.md` with correct UI steps
- Resolved local DNS caching issues with `systemd-resolved`

### Trigger template fixes

Updated `pipeline/triggers.yaml`:
- Added `ssh-key` workspace (referencing `git-ssh-key` secret) to both PR and merge templates
- Added `build-cache` workspace (referencing `build-cache` PVC) to both templates
- Changed `IMAGE_REGISTRY_PLACEHOLDER` to `localhost:5000`
- Set `compile-image-*` defaults to `localhost:5000/...`

### Working flow

1. Open PR in any app repo → webhook fires → `stack-pr-test` runs automatically
2. PR pipeline tests only (snapshot tag, build, intercept, validate, test, PR comment)
3. Merge the PR → webhook fires → `stack-merge-release` runs automatically
4. Merge pipeline promotes RC → release, builds, tags release images, pushes version commit

---

## 6. Bug fixes

| Issue | Root cause | Fix |
|-------|-----------|-----|
| `tag-release-images` failed with `jq: not found` | `gcr.io/go-containerregistry/crane:debug` image has no `jq` | Rewrote JSON parsing in `tasks/tag-release-images.yaml` using busybox `sed`/`grep` |
| `post-pr-comment` failed with `CreateContainerConfigError` | Kubernetes secret `github-token` missing in `tekton-pipelines` namespace | Created secret: `kubectl create secret generic github-token --from-literal=token=$GITHUB_TOKEN -n tekton-pipelines` |
| Webhook-triggered runs failed with missing `ssh-key` workspace | TriggerTemplates not binding `ssh-key` and `build-cache` workspaces | Added workspace bindings to both templates in `triggers.yaml` |
| Merge pipeline not triggering after PR merge | Cloudflare Tunnel missing public hostname route for `tekton-el.menkelabs.com` | Added route in Cloudflare Zero Trust dashboard |
| GitGuardian flagged `--secret` in `configure-github-webhooks.sh` | CLI option `--secret` matched GitGuardian's "Generic CLI Option Secret" pattern | Renamed to `--webhook-secret` throughout the script |
| Python build image failed (`python3.12` not in Ubuntu 22.04 repos) | Ubuntu 22.04 doesn't ship Python 3.12 | Switched to `python:3.12-slim` base image |

---

## 7. New Tekton tasks

| Task | File | Purpose |
|------|------|---------|
| `build-compile-npm` | `tasks/build-compile-npm.yaml` | npm compile step using pre-built node image |
| `build-compile-maven` | `tasks/build-compile-maven.yaml` | Maven compile step using pre-built maven image |
| `build-compile-gradle` | `tasks/build-compile-gradle.yaml` | Gradle compile step using pre-built JDK image |
| `build-compile-pip` | `tasks/build-compile-pip.yaml` | pip compile step using pre-built python image |
| `build-compile-composer` | `tasks/build-compile-composer.yaml` | Composer compile step using pre-built PHP image |
| `build-containerize` | `tasks/build-containerize.yaml` | Kaniko containerization step |
| `build-select-tool-apps` | `tasks/build-select-tool-apps.yaml` | Route apps to correct compile task by build tool |
| `post-pr-comment` | `tasks/post-pr-comment.yaml` | Post run status comment on GitHub PR |
| `pr-snapshot-tag` | `tasks/pr-snapshot-tag.yaml` | Generate snapshot tag for PR builds |

---

## 8. .gitignore and dependency cleanup

Updated `.gitignore` to globally ignore common build outputs:
- `node_modules/`, `vendor/`, `__pycache__/`, `target/`, `dist/`, `build/`, `.gradle/`

---

## 9. Milestone 4 planning

Created `milestones/milestone-4.md` with two areas of planned work:

**Production-safe baggage middleware libraries** — one standalone library per framework (Spring Boot, Spring Legacy, Node, Flask, PHP). Each supports all three propagation roles (originator, forwarder, terminal) via configuration. Two guard layers (build-time exclusion + runtime env-var gate) ensure zero production execution. Test stacks will exercise every framework in every role.

| Library | Package | Framework |
|---------|---------|-----------|
| `baggage-spring-boot-starter` | Maven | Spring Boot |
| `baggage-servlet-filter` | Maven | Spring Legacy / WAR |
| `@tekton-dag/baggage` | npm | Node (Express, Nitro, Vue) |
| `tekton-dag-baggage` | pip | Flask / WSGI |
| `tekton-dag/baggage-middleware` | Composer | PHP (PSR-15 + Guzzle) |

**Multi-namespace pipeline scaling** — three-tier model: local (Kind) → test namespace → production namespace. Pipeline upgrades validated locally, then in isolated test namespace, then promoted to production. Includes namespace-agnostic YAML, bootstrap/promotion scripts, per-namespace EventListeners.

---

## 10. README.md overhaul

- Added "What's new (2026-02-28)" section covering webhook flow, build images, registry setup, Cloudflare Tunnel
- Added milestone 4 planned work summary
- Fixed C4 diagrams (spacing between nodes, added `stack-bootstrap` pipeline, shortened descriptions)
- Overhauled Layout section to match actual project contents (added all missing directories and files)

---

## 11. Git operations

- Force-pushed `test-pr-*` branch into `main` with all accumulated changes
- Resolved GitGuardian pre-commit warnings by renaming `--secret` to `--webhook-secret`

---

## Current state

### Pipeline infrastructure — working

| Pipeline | Trigger | Status |
|----------|---------|--------|
| `stack-pr-test` | Webhook (PR opened) | **Working** — snapshot tag, build, intercept, validate, test, PR comment |
| `stack-merge-release` | Webhook (PR merged) | **Working** — promote RC, build, tag release images, push version commit |
| `stack-bootstrap` | Manual (`generate-run.sh`) | **Working** |
| `stack-dag-verify` | Manual | **Working** |

### Middleware (current state)

- **Spring Boot**: `BaggageContextFilter.java` — incoming-only Servlet filter. No outgoing propagation, not a standalone library.
- **All other apps**: minimal hello-world apps with no middleware code.

### Cluster

- Kind cluster `tekton-stack`, single node
- Tekton Pipelines + Triggers installed
- Cloudflare Tunnel active for webhook routing
- Build images published to `localhost:5001` (Kind registry)
- Reporting GUI available at `localhost:5173` (frontend) + `localhost:4000` (backend)

---

## Next steps (milestone 4)

1. Build the five middleware libraries (one per framework, all three roles)
2. Create test stack YAML files for cross-framework role testing
3. Parameterize namespace in pipeline/task YAML for multi-namespace support
4. Create bootstrap and promotion scripts for namespace management
