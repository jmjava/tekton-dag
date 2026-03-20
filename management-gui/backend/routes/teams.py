from flask import Blueprint, current_app, jsonify

bp = Blueprint("teams", __name__)


@bp.route("/api/teams")
def list_teams():
    registry = current_app.config["TEAM_REGISTRY"]
    return jsonify(registry.list_teams())
