"""Static acceptance checks for the M17.3 intercept product path."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_intercept_workflow_has_explicit_backend_cadence_and_evidence():
    workflow = (ROOT / ".github/workflows/intercept-e2e.yml").read_text()

    assert "pull_request:" in workflow
    assert '".github/workflows/intercept-e2e.yml"' in workflow
    assert '"helm/tekton-dag/**"' in workflow
    assert '"scripts/bootstrap-namespace.sh"' in workflow
    assert "workflow_dispatch:" in workflow
    assert "schedule:" in workflow
    assert "backend: [telepresence, mirrord]" in workflow
    assert "E2E_GIT_SSH_PRIVATE_KEY" in workflow
    assert "Require E2E SSH credential" not in workflow
    assert "public application repositories will use HTTPS" in workflow
    assert "kubectl create secret generic ssh-key-secret" in workflow
    assert "pod-security.kubernetes.io/enforce=privileged" in workflow
    assert "run-product-intercept-e2e.sh" in workflow
    assert "if: always()" in workflow
    assert "actions/upload-artifact@" in workflow
    assert "retention-days: 30" in workflow
    # Workflow-level expressions are evaluated before matrix expansion.
    assert "matrix." not in workflow.split("jobs:", 1)[0]


def test_product_script_covers_trigger_stackrun_tests_and_cleanup():
    script = (ROOT / "scripts/run-product-intercept-e2e.sh").read_text()

    assert "$API_URL/api/run" in script
    assert "Authorization: Bearer $API_MUTATION_TOKEN" in script
    assert "kubectl get stackrun" in script
    assert "status.pipelineRunName" in script
    assert "pipeline-results.json" in script
    assert "tekton.dev/pipelineTask=run-tests" in script
    assert 'pipeline_status" == "False"' in script
    assert "kubectl get pvc build-cache" in script
    assert "pr-traffic-evidence.log" in script
    assert "kubectl delete pipelinerun" in script
    assert "kubectl delete stackrun" in script


def test_mirrord_image_uses_kind_registry_consistently():
    pipeline = (ROOT / "pipeline/stack-pr-pipeline.yaml").read_text()
    task = (ROOT / "tasks/deploy-intercept-mirrord.yaml").read_text()
    expected = "localhost:5000/tekton-dag-build-mirrord:latest"

    assert expected in pipeline
    assert expected in task
    assert "localhost:5001/tekton-dag-build-mirrord" not in pipeline
    assert "localhost:5001/tekton-dag-build-mirrord" not in task


def test_app_clone_supports_public_https_without_ssh_key():
    task = (ROOT / "tasks/clone-app-repos.yaml").read_text()

    assert "CLONE_TRANSPORT=https" in task
    assert 'URL="https://github.com/${REPO}.git"' in task
    assert 'URL="git@github.com:${REPO}.git"' in task
    assert "ssh-key workspace must contain" not in task


def test_tekton_install_allows_source_and_build_cache_pvcs():
    install = (ROOT / "scripts/install-tekton.sh").read_text()

    assert "kubectl patch configmap feature-flags -n tekton-pipelines" in install
    assert '''-p '{"data":{"coschedule":"disabled"}}' '''.strip() in install
    assert "rollout status deployment/tekton-pipelines-webhook" in install
    assert "rollout status deployment/tekton-triggers-webhook" in install
    assert (
        install.index("rollout status deployment/tekton-triggers-webhook")
        < install.index('apply_with_retry -f "$TEKTON_TRIGGERS_INTERCEPTORS_URL"')
    )
    assert 'apply_with_retry -f "$MILESTONE_DIR/tasks/"' in install


def test_compile_pipeline_defaults_are_valid_container_images():
    for name in (
        "stack-bootstrap-pipeline.yaml",
        "stack-pr-pipeline.yaml",
        "stack-merge-pipeline.yaml",
    ):
        pipeline = (ROOT / "pipeline" / name).read_text()
        for image_param in ("npm", "maven", "gradle", "pip", "php"):
            marker = f"- name: compile-image-{image_param}"
            default = pipeline.split(marker, 1)[1].split("- name:", 1)[0]
            assert 'default: "ubuntu:22.04"' in default


def test_pipelinerun_builders_use_installed_build_cache_claim():
    go_builder = (ROOT / "operator/internal/pipeline/builder.go").read_text()
    python_builder = (ROOT / "orchestrator/pipelinerun_builder.py").read_text()

    assert '"claimName": "build-cache"' in go_builder
    assert '"claimName": "build-cache-pvc"' not in go_builder
    assert '"claimName": "build-cache"' in python_builder
    assert '"claimName": "build-cache-pvc"' not in python_builder


def test_pr_comment_token_is_optional_when_commenting_is_not_configured():
    task = (ROOT / "tasks/post-pr-comment.yaml").read_text()

    token_ref = task.split("secretKeyRef:", 1)[1].split("- name: GIT_URL", 1)[0]
    assert "key: token" in token_ref
    assert "optional: true" in token_ref
    assert 'if [ -z "$GITHUB_TOKEN" ]' in task
