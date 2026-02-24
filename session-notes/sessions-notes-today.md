# Session notes — Monday Feb 23, 2025

Summary of what we did today in the **tekton-dag** project.

---

## 1. Sample app repos for each application type

The pipeline runs Tekton PR scripts for DAGs built from many small application repos. We created **sample repos** for each application type in the plan and added them to the **jmjava** GitHub org as `tekton-dag-<name>`:

| Repo | Build tool | Used by stacks |
|------|------------|----------------|
| **tekton-dag-vue-fe** | npm | demo-fe, vendor-fe |
| **tekton-dag-spring-boot** | Maven | release-lifecycle-demo, demo-api, inventory-api |
| **tekton-dag-spring-boot-gradle** | Gradle | vendor-middleware |
| **tekton-dag-php** | Composer | vendor-adapter |
| **tekton-dag-spring-legacy** | Maven (WAR) | internal-api |
| **tekton-dag-flask** | pip | notifications-svc, analytics-api |

Each repo is a minimal but valid app (Dockerfile, tests where applicable) so the pipeline can clone, build, and run the DAG locally.

---

## 2. sample-repos directory and scripts

- **`sample-repos/`** — Added in the tekton-dag repo with a **README** that:
  - Explains sample apps are separate GitHub repos under jmjava
  - Lists clone commands for `~/github/jmjava` and all six repos (SSH URLs)
  - Includes a table of repo name, clone URL, and build tool

- **`scripts/create-and-push-sample-repos.sh`** — Script to create and/or push the sample repos. Supports `--dry-run` and optional app names. Can use `SAMPLE_REPOS_ROOT` (e.g. `~/github/jmjava`) when using clones instead of nested `sample-repos/`.

- **`.gitignore`** — Updated so nested app dirs under `sample-repos/` are treated as standalone repos: ignore `sample-repos/*/.git/`, `node_modules/`, `target/`, `build/`, `.gradle/`, `vendor/`, `__pycache__`, `.venv`, etc., so the pipeline can clone from GitHub and we don’t commit build artifacts from sample apps.

---

## 3. Stacks and version registry

- **`stacks/versions.yaml`** — Version registry for all apps (Stack One, Stack Two, standalone). Tracks `version` (e.g. `0.1.0-rc.0`) and `last-released` per app. Used as the default version set; overridable at run time via version-overrides.

- **Stack YAMLs** — stack-one, stack-two-vendor, single-app, single-flask-app, registry define the DAG and reference app repos as `repo: jmjava/tekton-dag-<name>`.

---

## 4. VS Code launch configs

- **`.vscode/launch.json`** — Added launch and attach configurations for local debugging of each app type:
  - Vue (demo-fe): npm run dev + Chrome debug
  - Spring Boot (release-lifecycle-demo): Java launch & attach (port 5005)
  - Spring Boot Gradle: Java launch & attach
  - PHP, Spring Legacy, Flask: corresponding launch/attach configs  
  Uses multi-root workspace folders (e.g. `tekton-dag-vue-fe`, `tekton-dag-spring-boot`) when those repos are opened alongside tekton-dag.

---

## 5. Session notes

- **`session-notes/`** directory created; this file is the first session note.

---

## Next steps (suggested)

- Clone the six app repos to `~/github/jmjava` and run the pipeline (e.g. `verify-dag-phase2.sh`) to confirm clone → resolve → build order.
- Run full PR or merge pipeline against a stack and confirm build order and deploy/validate params match the DAG (Phase 3 of the local verification plan).
