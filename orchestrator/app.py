"""
tekton-dag orchestration service.

Receives GitHub webhooks, resolves stacks, creates Tekton PipelineRuns.
Runs as an in-cluster pod alongside Tekton.
"""

import os
import logging

from flask import Flask

from routes import register_routes
from stack_resolver import StackResolver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orchestrator")


def create_app():
    app = Flask(__name__)

    app.config.update(
        NAMESPACE=os.environ.get("NAMESPACE", "tekton-pipelines"),
        TEAM_NAME=os.environ.get("TEAM_NAME", "default"),
        IMAGE_REGISTRY=os.environ.get("IMAGE_REGISTRY", "localhost:5000"),
        CACHE_REPO=os.environ.get("CACHE_REPO", "localhost:5000/kaniko-cache"),
        INTERCEPT_BACKEND=os.environ.get("INTERCEPT_BACKEND", "telepresence"),
        MAX_PARALLEL_BUILDS=int(os.environ.get("MAX_PARALLEL_BUILDS", "5")),
        GIT_URL=os.environ.get("GIT_URL", "https://github.com/jmjava/tekton-dag.git"),
        GIT_REVISION=os.environ.get("GIT_REVISION", "main"),
        STACK_FILE=os.environ.get("STACK_FILE", "stacks/stack-one.yaml"),
        WEBHOOK_SECRET_NAME=os.environ.get("WEBHOOK_SECRET_NAME", "github-webhook-secret"),
    )

    stacks_dir = os.environ.get("STACKS_DIR", "/stacks")
    teams_dir = os.environ.get("TEAMS_DIR", "/teams")
    resolver = StackResolver(stacks_dir=stacks_dir, teams_dir=teams_dir)
    app.config["RESOLVER"] = resolver

    register_routes(app)

    logger.info(
        "Orchestrator started: team=%s ns=%s registry=%s",
        app.config["TEAM_NAME"],
        app.config["NAMESPACE"],
        app.config["IMAGE_REGISTRY"],
    )

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8080, debug=True)
