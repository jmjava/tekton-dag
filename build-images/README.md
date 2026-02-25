# Build images (one per tool)

Pre-baked container images used by the `build-stack-apps` task for compiling apps. One image per build tool so each compile step runs in a minimal image with only the tools it needs.

## Images

| Image | Dockerfile | Contents |
|-------|------------|----------|
| `tekton-dag-build-node` | `Dockerfile.node` | Node 22 (NodeSource), npm, jq, curl |
| `tekton-dag-build-maven` | `Dockerfile.maven` | **JDK pre-installed** (OpenJDK 21), Maven, jq, curl |
| `tekton-dag-build-gradle` | `Dockerfile.gradle` | **JDK pre-installed** (OpenJDK 21), jq, curl. Apps use `./gradlew` from the repo. |
| `tekton-dag-build-python` | `Dockerfile.python` | Python 3.12, venv, pip, jq, curl |
| `tekton-dag-build-php` | `Dockerfile.php` | PHP 8.3 (ondrej PPA), Composer, jq, curl |

Java images (maven, gradle) ship with JDK already in the image; the task does not install JDK at runtime when using these images.

## Build and push

From this directory:

```bash
./build-and-push.sh [REGISTRY] [TAG]
```

- **REGISTRY** (default: `localhost:5000`) — e.g. Kind’s local registry or `ghcr.io/your-org`.
- **TAG** (default: `latest`).

Example for Kind:

```bash
./build-and-push.sh localhost:5000 latest
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

## Kind

If you use Kind with a local registry (e.g. `scripts/kind-with-registry.sh`), push these images to `localhost:5000` so cluster nodes can pull them. Run `./build-and-push.sh` once after bringing up the cluster.
