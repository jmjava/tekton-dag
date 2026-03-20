from flask import Blueprint, current_app, jsonify

bp = Blueprint("stacks", __name__)


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
