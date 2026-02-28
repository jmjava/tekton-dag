#!/usr/bin/env bash
set -euo pipefail

# generate-run.sh — Generate and optionally apply a PipelineRun for
# a given stack, triggered either as a PR test or a merge release.
#
# Usage:
#   ./generate-run.sh --mode pr    --repo demo-fe --pr 42
#   ./generate-run.sh --mode merge --repo demo-fe
#   ./generate-run.sh --mode pr    --repo demo-fe --pr 42 \
#       --version-overrides '{"demo-fe":"2.0.0-rc.0"}'
#
# Options:
#   --mode               pr | merge
#   --stack              Stack file name (e.g. stack-one.yaml)
#   --app                App name that changed
#   --repo               Repo name (alternative to --stack + --app; uses registry.yaml)
#   --pr                 PR number (required for pr mode)
#   --version-overrides  JSON map of app → version overrides
#   --git-url            Override git URL
#   --git-revision       Override git revision (platform repo; for PR mode, use --app-revision so the changed app repo is checked out at its PR branch)
#   --app-revision       For PR mode: app:revision (e.g. demo-fe:my-pr-branch). Can be repeated. Builds app-revisions JSON for the pipeline.
#   --app-revisions-json Internal: full JSON for app-revisions (used when re-invoking with --apply so revisions are preserved).
#   --registry           Override image registry (use any: Docker Hub, GCR, local)
#   --build-images       Use dedicated build images (default: true when registry set). Run build-images/build-and-push.sh once.
#   --no-build-images    Use bare ubuntu:22.04 and install Node/Maven/etc. in-pod each run (slower).
#   --storage-class      PVC storage class (default: gp3 for AWS; use standard or omit for kind/minikube)
#   --apply              kubectl create the PipelineRun immediately
#   --dry-run            Print the YAML without applying

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACKS_DIR="$SCRIPT_DIR/../stacks"
REGISTRY_FILE="$STACKS_DIR/registry.yaml"

die()  { echo "ERROR: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "$1 is required"; }
need yq
need jq

MODE=""
STACK=""
APP=""
REPO=""
PR=""
GIT_URL=""
GIT_REV=""
APP_REVISIONS="{}"
IMAGE_REGISTRY=""
# Empty = use cluster default (Kind, minikube). Set to gp3 (or other) for AWS.
STORAGE_CLASS="${STORAGE_CLASS:-}"
VERSION_OVERRIDES="{}"
GIT_SSH_SECRET_NAME="${GIT_SSH_SECRET_NAME:-git-ssh-key}"
APPLY=false
# Default: use pre-built build images (Node/Maven/etc.) so compile steps load quickly. Use --no-build-images for bare ubuntu:22.04.
BUILD_IMAGES="${BUILD_IMAGES:-true}"
BUILD_IMAGE_TAG="${BUILD_IMAGE_TAG:-latest}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)               MODE="$2"; shift 2 ;;
    --stack)              STACK="$2"; shift 2 ;;
    --app)                APP="$2"; shift 2 ;;
    --repo)               REPO="$2"; shift 2 ;;
    --pr)                 PR="$2"; shift 2 ;;
    --version-overrides)  VERSION_OVERRIDES="$2"; shift 2 ;;
    --git-url)            GIT_URL="$2"; shift 2 ;;
    --git-revision)       GIT_REV="$2"; shift 2 ;;
    --app-revision)       _app="${2%%:*}"; _rev="${2#*:}"; [[ "$_app" != "$2" && -n "$_rev" ]] || die "--app-revision must be app:revision (e.g. demo-fe:my-branch)"; APP_REVISIONS=$(echo "$APP_REVISIONS" | jq -c --arg a "$_app" --arg r "$_rev" '. + {($a): $r}'); shift 2 ;;
    --app-revisions-json) APP_REVISIONS="$2"; shift 2 ;;
    --registry)           IMAGE_REGISTRY="$2"; shift 2 ;;
    --build-images)       BUILD_IMAGES=true; shift ;;
    --no-build-images)    BUILD_IMAGES=false; shift ;;
    --storage-class)      STORAGE_CLASS="$2"; shift 2 ;;
    --ssh-secret)         GIT_SSH_SECRET_NAME="$2"; shift 2 ;;
    --apply)              APPLY=true; shift ;;
    --dry-run)            APPLY=false; shift ;;
    *)                    die "Unknown option: $1" ;;
  esac
done

[[ -n "$MODE" ]] || die "--mode is required (pr or merge)"

# Resolve stack and app from repo if needed
if [[ -n "$REPO" && -z "$STACK" ]]; then
  [[ -f "$REGISTRY_FILE" ]] || die "Registry file not found: $REGISTRY_FILE"
  STACK=$(yq ".repos.\"${REPO}\".stack" "$REGISTRY_FILE")
  [[ "$STACK" != "null" ]] || die "Repo '$REPO' not found in registry"
  APP="${APP:-$REPO}"
fi

[[ -n "$STACK" ]] || die "--stack or --repo is required"

STACK_PATH="stacks/$STACK"
[[ -f "$STACKS_DIR/$STACK" ]] || die "Stack file not found: $STACKS_DIR/$STACK"

# Defaults: git-url is the platform repo (tekton-dag) with stacks/ and versions; app repos are cloned separately from stack .apps[].repo (e.g. jmjava/tekton-dag-vue-fe)
# Use main for platform repo so the pipeline can always fetch from remote; local SHA may not exist on origin and causes "couldn't find remote ref"
GIT_URL="${GIT_URL:-https://github.com/jmjava/tekton-dag.git}"
GIT_REV="${GIT_REV:-main}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-localhost:5001}"
# Defensive: strip stray trailing '}' (e.g. from env or template copy-paste) so Kaniko destination is valid
while [[ "${IMAGE_REGISTRY: -1}" == "}" ]]; do IMAGE_REGISTRY="${IMAGE_REGISTRY%?}"; done
# Containerd certs.d maps localhost:5000 -> kind-registry:5000 internally; use localhost:5000 for all image refs
COMPILE_IMAGE_REGISTRY="${IMAGE_REGISTRY}"
PIPELINE_IMAGE_REGISTRY="${IMAGE_REGISTRY}"
if [[ "$IMAGE_REGISTRY" == "localhost:5001" ]]; then
  COMPILE_IMAGE_REGISTRY="localhost:5000"
  PIPELINE_IMAGE_REGISTRY="localhost:5000"
fi

if [[ "$MODE" == "pr" ]]; then
  [[ -n "$PR" ]] || die "--pr is required for pr mode"
  [[ -n "$APP" ]] || die "PR mode tests one app at a time: --app is required (e.g. --app demo-fe)"
  # When PR is in app repo (app-revisions set), resolve app repo URL so post-pr-comment targets the right repo
  PR_REPO_URL=""
  if [[ "$APP_REVISIONS" != "{}" && -n "$APP" ]]; then
    REPO_SLUG=$(yq -r ".apps[] | select(.name == \"$APP\") | .repo" "$STACKS_DIR/$STACK" 2>/dev/null || true)
    [[ -n "$REPO_SLUG" && "$REPO_SLUG" != "null" ]] && PR_REPO_URL="https://github.com/${REPO_SLUG}.git"
  fi

  cat <<EOF
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: stack-pr-${PR}-
  namespace: tekton-pipelines
spec:
  pipelineRef:
    name: stack-pr-test
  taskRunTemplate:
    serviceAccountName: tekton-pr-sa
    podTemplate:
      securityContext:
        fsGroup: 65532
  params:
    - name: git-url
      value: "${GIT_URL}"
    - name: git-revision
      value: "${GIT_REV}"
    - name: stack-file
      value: "${STACK_PATH}"
    - name: changed-app
      value: "${APP}"
    - name: pr-number
      value: "${PR}"
    - name: app-revisions
      value: '${APP_REVISIONS}'
    - name: pr-repo-url
      value: "${PR_REPO_URL}"
    - name: image-registry
      value: "${PIPELINE_IMAGE_REGISTRY}"
    - name: version-overrides
      value: '${VERSION_OVERRIDES}'
    $([ "$BUILD_IMAGES" = "true" ] && [ -n "$IMAGE_REGISTRY" ] && echo "
    - name: compile-image-npm
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-node:${BUILD_IMAGE_TAG}\"
    - name: compile-image-maven
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-maven:${BUILD_IMAGE_TAG}\"
    - name: compile-image-gradle
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-gradle:${BUILD_IMAGE_TAG}\"
    - name: compile-image-pip
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-python:${BUILD_IMAGE_TAG}\"
    - name: compile-image-php
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-php:${BUILD_IMAGE_TAG}\"
    ")
  workspaces:
    - name: shared-workspace
      volumeClaimTemplate:
        spec:
          accessModes: [ReadWriteOnce]
          $([ -n "$STORAGE_CLASS" ] && echo "storageClassName: $STORAGE_CLASS")
          resources:
            requests:
              storage: 5Gi
    - name: ssh-key
      secret:
        secretName: "${GIT_SSH_SECRET_NAME}"
    - name: build-cache
      persistentVolumeClaim:
        claimName: build-cache
EOF

elif [[ "$MODE" == "merge" ]]; then

  cat <<EOF
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: stack-merge-
  namespace: tekton-pipelines
spec:
  pipelineRef:
    name: stack-merge-release
  taskRunTemplate:
    serviceAccountName: tekton-pr-sa
    podTemplate:
      securityContext:
        fsGroup: 65532
  params:
    - name: git-url
      value: "${GIT_URL}"
    - name: git-revision
      value: "${GIT_REV}"
    - name: stack-file
      value: "${STACK_PATH}"
    - name: changed-app
      value: "${APP}"
    - name: image-registry
      value: "${PIPELINE_IMAGE_REGISTRY}"
    - name: version-overrides
      value: '${VERSION_OVERRIDES}'
    $([ "$BUILD_IMAGES" = "true" ] && [ -n "$IMAGE_REGISTRY" ] && echo "
    - name: compile-image-npm
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-node:${BUILD_IMAGE_TAG}\"
    - name: compile-image-maven
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-maven:${BUILD_IMAGE_TAG}\"
    - name: compile-image-gradle
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-gradle:${BUILD_IMAGE_TAG}\"
    - name: compile-image-pip
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-python:${BUILD_IMAGE_TAG}\"
    - name: compile-image-php
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-php:${BUILD_IMAGE_TAG}\"
    ")
  workspaces:
    - name: shared-workspace
      volumeClaimTemplate:
        spec:
          accessModes: [ReadWriteOnce]
          $([ -n "$STORAGE_CLASS" ] && echo "storageClassName: $STORAGE_CLASS")
          resources:
            requests:
              storage: 5Gi
    - name: ssh-key
      secret:
        secretName: "${GIT_SSH_SECRET_NAME}"
    - name: build-cache
      persistentVolumeClaim:
        claimName: build-cache
EOF

elif [[ "$MODE" == "merge" ]]; then

  cat <<EOF
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: stack-merge-
  namespace: tekton-pipelines
spec:
  pipelineRef:
    name: stack-merge-release
  taskRunTemplate:
    serviceAccountName: tekton-pr-sa
    podTemplate:
      securityContext:
        fsGroup: 65532
  params:
    - name: git-url
      value: "${GIT_URL}"
    - name: git-revision
      value: "${GIT_REV}"
    - name: stack-file
      value: "${STACK_PATH}"
    - name: changed-app
      value: "${APP}"
    - name: image-registry
      value: "${PIPELINE_IMAGE_REGISTRY}"
    - name: version-overrides
      value: '${VERSION_OVERRIDES}'
    $([ "$BUILD_IMAGES" = "true" ] && [ -n "$IMAGE_REGISTRY" ] && echo "
    - name: compile-image-npm
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-node:${BUILD_IMAGE_TAG}\"
    - name: compile-image-maven
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-maven:${BUILD_IMAGE_TAG}\"
    - name: compile-image-gradle
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-gradle:${BUILD_IMAGE_TAG}\"
    - name: compile-image-pip
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-python:${BUILD_IMAGE_TAG}\"
    - name: compile-image-php
      value: \"${COMPILE_IMAGE_REGISTRY}/tekton-dag-build-php:${BUILD_IMAGE_TAG}\"
    ")
  workspaces:
    - name: shared-workspace
      volumeClaimTemplate:
        spec:
          accessModes: [ReadWriteOnce]
          $([ -n "$STORAGE_CLASS" ] && echo "storageClassName: $STORAGE_CLASS")
          resources:
            requests:
              storage: 5Gi
    - name: ssh-key
      secret:
        secretName: "${GIT_SSH_SECRET_NAME}"
    - name: build-cache
      persistentVolumeClaim:
        claimName: build-cache
EOF

else
  die "Unknown mode: $MODE (must be pr or merge)"
fi

# Apply if requested (re-invoke with all params so app-revisions and ssh-secret are preserved)
if [[ "$APPLY" == "true" ]]; then
  echo "---"
  echo "# Applying PipelineRun..."
  "$0" --mode "$MODE" --stack "$STACK" --app "$APP" \
    ${PR:+--pr "$PR"} \
    --app-revisions-json "$APP_REVISIONS" \
    --version-overrides "$VERSION_OVERRIDES" \
    --git-url "$GIT_URL" --git-revision "$GIT_REV" \
    --registry "$IMAGE_REGISTRY" \
    --ssh-secret "$GIT_SSH_SECRET_NAME" \
    $([ "$BUILD_IMAGES" = "true" ] && echo "--build-images ") \
    --storage-class "$STORAGE_CLASS" | kubectl create -f -
fi
