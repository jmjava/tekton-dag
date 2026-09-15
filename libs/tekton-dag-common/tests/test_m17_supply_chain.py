"""Static acceptance checks for M17.8 supply-chain automation."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def test_dependabot_covers_all_supported_ecosystems_and_directories():
    config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())
    updates = config["updates"]

    assert {entry["package-ecosystem"] for entry in updates} == {
        "composer",
        "github-actions",
        "gomod",
        "maven",
        "npm",
        "pip",
    }

    directories = {
        ecosystem: set(entry.get("directories", [entry.get("directory")]))
        for entry in updates
        if (ecosystem := entry["package-ecosystem"]) in {"npm", "pip", "maven"}
    }
    assert directories["npm"] == {
        "/management-gui/frontend",
        "/reporting-gui/frontend",
        "/reporting-gui/backend",
        "/libs/baggage-node",
        "/docs/demos/slides",
    }
    assert "/" in directories["pip"]
    assert "/docs/demos" in directories["pip"]
    assert "/documentation-generator/video-framework" in directories["pip"]
    assert directories["maven"] == {
        "/libs/baggage-spring-boot-starter",
        "/libs/baggage-servlet-filter",
    }


def test_dependency_review_rejects_new_high_runtime_findings():
    workflow = (ROOT / ".github/workflows/dependency-review.yml").read_text()

    assert "actions/dependency-review-action@" in workflow
    assert "fail-on-severity: high" in workflow
    assert "fail-on-scopes: runtime,unknown" in workflow
    assert "pull_request_target" not in workflow


def test_trivy_scans_filesystem_and_production_images():
    workflow = (ROOT / ".github/workflows/supply-chain-scan.yml").read_text()

    assert "version: v0.74.0" in workflow
    assert "scanners: vuln,secret" in workflow
    assert "severity: HIGH,CRITICAL" in workflow
    assert workflow.count('exit-code: "1"') == 2
    assert "security-events: write" in workflow
    assert "github/codeql-action/upload-sarif@" in workflow
    assert "name: operator" in workflow
    assert "name: orchestrator" in workflow
    assert "name: management-backend" in workflow


def test_all_workflow_actions_are_pinned_to_full_shas():
    uses_pattern = re.compile(r"^\s*uses:\s*([^@\s]+)@([^\s#]+)", re.MULTILINE)
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        for action, revision in uses_pattern.findall(workflow.read_text()):
            assert re.fullmatch(r"[0-9a-f]{40}", revision), (
                f"{workflow}: {action}@{revision} is mutable"
            )


def test_runtime_manifests_use_patched_dependency_floors():
    go_mod = (ROOT / "operator/go.mod").read_text()
    operator_image = (ROOT / "operator/Dockerfile").read_text()
    orchestrator_runtime = (ROOT / "orchestrator/requirements.txt").read_text()
    orchestrator_dev = (ROOT / "orchestrator/requirements-dev.txt").read_text()
    spring = (ROOT / "libs/baggage-spring-boot-starter/pom.xml").read_text()

    assert "go 1.26.0" in go_mod
    assert "google.golang.org/grpc v1.83.2" in go_mod
    assert "golang.org/x/net v0.59.0" in go_mod
    assert "FROM docker.io/golang:1.26.8" in operator_image
    assert "pytest" not in orchestrator_runtime
    assert "pytest>=9.0.3,<10.0" in orchestrator_dev
    assert "<spring-boot.version>4.1.1</spring-boot.version>" in spring
    assert "<tomcat.version>11.0.25</tomcat.version>" in spring
