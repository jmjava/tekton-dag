#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# generate-run.sh — Generate and optionally apply a StackRun (operator)
# for a given stack. Raw PipelineRun emit (--pipeline-run) was removed in M16.

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
#   --git-revision       Override git revision
#   --app-revision       For PR mode: app:revision (e.g. demo-fe:my-pr-branch)
#   --app-revisions-json Internal: full JSON for app-revisions
#   --registry           Override image registry
#   --build-images       Use dedicated build images (default: true)
#   --no-build-images    Use bare ubuntu:22.04
#   --namespace          Target namespace (default: tekton-pipelines)
#   --storage-class      PVC storage class
#   --intercept-backend  telepresence (default) | mirrord (M7)
#   --apply              kubectl create the StackRun
#   --dry-run            Print the YAML without applying

REGISTRY_FILE="$STACKS_DIR/registry.yaml"

need yq
need jq

MODE=""
STACK=""
APP=""
REPO=""
PR=""
APP_REVISIONS="{}"
_IMAGE_REGISTRY=""
STORAGE_CLASS="${STORAGE_CLASS:-}"
VERSION_OVERRIDES="{}"
APPLY=false
BUILD_IMAGES="${BUILD_IMAGES:-true}"
BUILD_IMAGE_TAG="${BUILD_IMAGE_TAG:-latest}"
INTERCEPT_BACKEND="${INTERCEPT_BACKEND:-telepresence}"

if [[ "${GENERATE_PIPELINE_RUN:-false}" == "true" ]]; then
  die "--pipeline-run / GENERATE_PIPELINE_RUN was removed in M16; emit a StackRun (default) instead"
fi

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
    --registry)           _IMAGE_REGISTRY="$2"; shift 2 ;;
    --build-images)       BUILD_IMAGES=true; shift ;;
    --no-build-images)    BUILD_IMAGES=false; shift ;;
    --storage-class)      STORAGE_CLASS="$2"; shift 2 ;;
    --namespace)          NAMESPACE="$2"; shift 2 ;;
    --ssh-secret)         GIT_SSH_SECRET_NAME="$2"; shift 2 ;;
    --intercept-backend)  INTERCEPT_BACKEND="$2"; shift 2 ;;
    --apply)              APPLY=true; shift ;;
    --dry-run)            APPLY=false; shift ;;
    --pipeline-run)       die "--pipeline-run was removed in M16; emit a StackRun (default) instead" ;;
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

GIT_URL="${GIT_URL:-$GIT_URL}"
GIT_REV="${GIT_REV:-$GIT_REVISION}"
[[ -n "$_IMAGE_REGISTRY" ]] && IMAGE_REGISTRY="$_IMAGE_REGISTRY"
# Defensive: strip stray trailing '}' (e.g. from env or template copy-paste) so Kaniko destination is valid
while [[ "${IMAGE_REGISTRY: -1}" == "}" ]]; do IMAGE_REGISTRY="${IMAGE_REGISTRY%?}"; done
# Containerd certs.d maps localhost:5000 -> kind-registry:5000 internally; use localhost:5000 for all image refs
COMPILE_IMAGE_REGISTRY="${IMAGE_REGISTRY}"
PIPELINE_IMAGE_REGISTRY="${IMAGE_REGISTRY}"
if [[ "$IMAGE_REGISTRY" == "localhost:5001" ]]; then
  COMPILE_IMAGE_REGISTRY="localhost:5000"
  PIPELINE_IMAGE_REGISTRY="localhost:5000"
fi

STACK_REF="${STACK%.yaml}"
STACK_REF="${STACK_REF%.yml}"

if [[ "$MODE" == "pr" ]]; then
  [[ -n "$PR" ]] || die "--pr is required for pr mode"
  [[ -n "$APP" ]] || die "PR mode tests one app at a time: --app is required (e.g. --app demo-fe)"
  PR_REPO_URL=""
  if [[ "$APP_REVISIONS" != "{}" && -n "$APP" ]]; then
    REPO_SLUG=$(yq -r ".apps[] | select(.name == \"$APP\") | .repo" "$STACKS_DIR/$STACK" 2>/dev/null || true)
    [[ -n "$REPO_SLUG" && "$REPO_SLUG" != "null" ]] && PR_REPO_URL="https://github.com/${REPO_SLUG}.git"
  fi
  cat <<EOF
apiVersion: tektondag.io/v1alpha1
kind: StackRun
metadata:
  generateName: stackrun-pr-
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/part-of: tekton-job-standardization
    tektondag.io/mode: pr
spec:
  mode: pr
  stackFile: ${STACK_PATH}
  stackRef: ${STACK_REF}
  gitUrl: ${GIT_URL}
  gitRevision: ${GIT_REV}
  changedApp: ${APP}
  prNumber: ${PR}
  appRevisions: '${APP_REVISIONS}'
  prRepoUrl: "${PR_REPO_URL}"
  imageRegistry: ${PIPELINE_IMAGE_REGISTRY}
  interceptBackend: ${INTERCEPT_BACKEND}
EOF
elif [[ "$MODE" == "merge" ]]; then
  cat <<EOF
apiVersion: tektondag.io/v1alpha1
kind: StackRun
metadata:
  generateName: stackrun-merge-
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/part-of: tekton-job-standardization
    tektondag.io/mode: merge
spec:
  mode: merge
  stackFile: ${STACK_PATH}
  stackRef: ${STACK_REF}
  gitUrl: ${GIT_URL}
  gitRevision: ${GIT_REV}
  changedApp: ${APP}
  imageRegistry: ${PIPELINE_IMAGE_REGISTRY}
EOF
else
  die "Unknown mode: $MODE (must be pr or merge)"
fi

if [[ "$APPLY" == "true" ]]; then
  echo "---"
  echo "# Applying StackRun..."
  "$0" --mode "$MODE" --stack "$STACK" --app "$APP" \
    ${PR:+--pr "$PR"} \
    --intercept-backend "$INTERCEPT_BACKEND" \
    --app-revisions-json "$APP_REVISIONS" \
    --version-overrides "$VERSION_OVERRIDES" \
    --git-url "$GIT_URL" --git-revision "$GIT_REV" \
    --registry "$IMAGE_REGISTRY" \
    --namespace "$NAMESPACE" \
    --ssh-secret "$GIT_SSH_SECRET_NAME" \
    $([ "$BUILD_IMAGES" = "true" ] && echo "--build-images ") \
    --storage-class "$STORAGE_CLASS" | kubectl create -f -
fi
