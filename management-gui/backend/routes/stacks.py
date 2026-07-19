import sys
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

import k8s_client

bp = Blueprint("stacks", __name__)

# Editable / sibling checkout: allow import without requiring a prior pip install.
_COMMON = Path(__file__).resolve().parents[3] / "libs" / "tekton-dag-common"
if _COMMON.is_dir() and str(_COMMON) not in sys.path:
    sys.path.insert(0, str(_COMMON))

try:
    from tekton_dag_common.deploy_injection import (
        injection_summary,
        validate_injection_refs,
    )
except ImportError:  # pragma: no cover
    injection_summary = None
    validate_injection_refs = None


@bp.route("/api/teams/<team>/stacks")
def list_stacks(team):
    registry = current_app.config["TEAM_REGISTRY"]
    team_cfg = registry.get_team(team)
    if not team_cfg:
        return jsonify({"error": f"Unknown team: {team}"}), 404

    resolver = current_app.config["STACK_RESOLVER"]
    allowed = team_cfg.get("stacks")
    return jsonify(resolver.list_stacks(allowed_stacks=allowed))


@bp.route("/api/teams/<team>/stacks/<path:stack_file>/dag")
def get_dag(team, stack_file):
    registry = current_app.config["TEAM_REGISTRY"]
    team_cfg = registry.get_team(team)
    if not team_cfg:
        return jsonify({"error": f"Unknown team: {team}"}), 404

    allowed = team_cfg.get("stacks", [])
    if allowed and stack_file not in allowed:
        return jsonify({"error": f"Stack {stack_file} not allowed for team {team}"}), 403

    resolver = current_app.config["STACK_RESOLVER"]
    dag = resolver.get_dag(stack_file)
    if dag is None:
        return jsonify({"error": f"Stack not found: {stack_file}"}), 404
    return jsonify(dag)


@bp.route("/api/teams/<team>/apps/<app_name>/injection-status")
def app_injection_status(team, app_name):
    """
    Secrets/config injection plan + present/missing status for an app (M13).

    Uses full stack app dicts (find_app) so secrets/config blocks are visible.
    """
    if injection_summary is None or validate_injection_refs is None:
        return jsonify({"error": "tekton_dag_common.deploy_injection unavailable"}), 501

    registry = current_app.config["TEAM_REGISTRY"]
    team_cfg = registry.get_team(team)
    if not team_cfg:
        return jsonify({"error": f"Unknown team: {team}"}), 404

    resolver = current_app.config["STACK_RESOLVER"]
    allowed = team_cfg.get("stacks")
    found = resolver.find_app(app_name, allowed_stacks=allowed)
    if not found:
        return jsonify({"error": f"unknown app: {app_name}"}), 404

    app = found["app"]
    context, default_ns = registry.resolve_context(team)
    ns = request.args.get("namespace") or app.get("namespace") or default_ns
    summary = injection_summary(app)
    try:
        existing_secrets = k8s_client.list_secret_names(context, ns)
        existing_cms = k8s_client.list_configmap_names(context, ns)
    except Exception as exc:
        return jsonify({"error": f"kubernetes lookup failed: {exc}"}), 503

    errors = validate_injection_refs(
        app,
        existing_secrets=existing_secrets,
        existing_configmaps=existing_cms,
    )
    return jsonify({
        "app": app_name,
        "team": team,
        "namespace": ns,
        "stack_file": found["stack_file"],
        "ok": len(errors) == 0,
        "errors": errors,
        "secrets": {
            name: ("present" if name in existing_secrets else "missing")
            for name in summary["secrets"]
        },
        "configmaps": {
            name: ("present" if name in existing_cms else "missing")
            for name in summary["configmaps"]
        },
        "injection": summary,
    })
