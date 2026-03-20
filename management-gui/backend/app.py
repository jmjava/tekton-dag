"""
Tekton DAG Management GUI — Flask backend.

Serves team-scoped APIs for pipeline runs, stacks, triggers, and Git repos.
Uses the Kubernetes Python client directly (no kubectl dependency).

Deployment modes (controlled by TEAM_NAME env var):
  TEAM_NAME=*       → centralized: loads all teams, frontend shows team switcher
  TEAM_NAME=default → per-team: loads one team, frontend hides switcher
"""

import os
import logging
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from team_registry import TeamRegistry
from stack_resolver import StackResolver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mgmt")


def _resolve_dir(env_var, default_relative):
    """Resolve a directory from env var or relative to the tekton-dag repo."""
    val = os.environ.get(env_var)
    if val:
        return val
    repo_root = Path(__file__).resolve().parent.parent.parent
    return str(repo_root / default_relative)


def create_app():
    app = Flask(__name__)
    CORS(app)

    team_name = os.environ.get("TEAM_NAME", "*")
    teams_dir = _resolve_dir("TEAMS_DIR", "teams")
    stacks_dir = _resolve_dir("STACKS_DIR", "stacks")

    registry = TeamRegistry(teams_dir=teams_dir, team_filter=team_name)
    resolver = StackResolver(stacks_dir=stacks_dir)

    app.config["TEAM_REGISTRY"] = registry
    app.config["STACK_RESOLVER"] = resolver

    from routes.health import bp as health_bp
    from routes.teams import bp as teams_bp
    from routes.pipelines import bp as pipelines_bp
    from routes.stacks import bp as stacks_bp
    from routes.repos import bp as repos_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(pipelines_bp)
    app.register_blueprint(stacks_bp)
    app.register_blueprint(repos_bp)

    logger.info(
        "Management GUI backend started: team_filter=%s teams_dir=%s stacks_dir=%s",
        team_name, teams_dir, stacks_dir,
    )

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    create_app().run(host="0.0.0.0", port=port, debug=True)
