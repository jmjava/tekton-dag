"""
Shared pytest fixtures for orchestrator tests.

Ensures the orchestrator package (sibling of tests/) is importable as top-level
modules: routes, stack_resolver, k8s_client, etc.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from flask import Flask

ORCH_ROOT = Path(__file__).resolve().parent.parent
if str(ORCH_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCH_ROOT))


@pytest.fixture
def flask_app():
    """Minimal Flask app with routes and a mock StackResolver."""
    from routes import register_routes

    app = Flask(__name__)
    app.config.update(
        NAMESPACE="test-namespace",
        TEAM_NAME="alpha",
        IMAGE_REGISTRY="registry.example.com:5000",
        CACHE_REPO="registry.example.com:5000/kaniko-cache",
        INTERCEPT_BACKEND="telepresence",
        MAX_PARALLEL_BUILDS=5,
        GIT_URL="https://github.com/org/tekton-dag.git",
        GIT_REVISION="main",
        STACK_FILE="stacks/stack-one.yaml",
        WEBHOOK_SECRET_NAME="github-webhook-secret",
    )
    resolver = MagicMock(name="StackResolver")
    resolver.list_stacks.return_value = [
        {
            "stack_file": "stacks/demo.yaml",
            "name": "demo",
            "description": "d",
            "apps": [{"name": "fe", "repo": "org/fe", "role": "frontend"}],
        }
    ]
    resolver.list_teams.return_value = {"team-a": {"repos": []}}
    resolver.resolve_repo.return_value = {
        "stack_file": "stacks/demo.yaml",
        "app_name": "fe",
        "repo": "org/demo-fe",
    }
    app.config["RESOLVER"] = resolver
    register_routes(app)
    return app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()
