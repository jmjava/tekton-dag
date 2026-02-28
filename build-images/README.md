# Build images (one per tool)

Pre-baked container images used by the `build-stack-apps` task for compiling apps. One image per build tool so each compile step runs in a minimal image with only the tools it needs.

## Images

| Image | Dockerfile | Contents |
|-------|------------|----------|
| `tekton-dag-build-node` | `Dockerfile.node` | Official `node:22-slim` + jq, curl |
| `tekton-dag-build-maven` | `Dockerfile.maven` | Official `maven:3.9-eclipse-temurin-21` + jq, curl |
| `tekton-dag-build-gradle` | `Dockerfile.gradle` | Official `eclipse-temurin:21-jdk` + jq, curl. Apps use `./gradlew` from the repo. |
| `tekton-dag-build-python` | `Dockerfile.python` | Official `python:3.12-slim` + jq, curl |
| `tekton-dag-build-php` | `Dockerfile.php` | Official `php:8.3-cli` + zip ext, Composer, jq, curl |

Java images (maven, gradle) ship with JDK already in the image; the task does not install JDK at runtime when using these images.

## Build and push

From this directory:

```bash
./build-and-push.sh [REGISTRY] [TAG]
```

- **REGISTRY** (default: `localhost:5001` for Kind test env) — override for other registries.
- **TAG** (default: `latest`).

From repo root (defaults to Kind registry on port 5001):

```bash
./scripts/publish-build-images.sh
```

Example for GHCR:

```bash
./build-and-push.sh ghcr.io/your-org latest
```

The script builds and pushes all five images and prints the full image refs to pass as `compile-image-*` params.

## How the task uses them

The `build-stack-apps` task has five optional params:

- `compile-image-npm`
- `compile-image-maven`
- `compile-image-gradle`
- `compile-image-pip`
- `compile-image-php`

When a param is set, the corresponding compile step uses that image and does not install the tool at runtime. When unset, the step falls back to `ubuntu:22.04` and installs only that tool (backward compatible).

Pipelines can pass these refs explicitly or derive them from a single registry + tag (e.g. `$REGISTRY/tekton-dag-build-maven:$TAG`). See the main repo README and pipeline docs for wiring.

## Kind (test env default)

The default publish target is **localhost:5001** — the Kind registry on the host. The cluster pulls via `kind-registry:5000`. Run `./scripts/publish-build-images.sh` with no args to push there. Override with the first argument (e.g. `./scripts/publish-build-images.sh ghcr.io/your-org`) for other registries.
