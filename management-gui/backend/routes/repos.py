from flask import Blueprint, current_app, jsonify, request

import github_client

bp = Blueprint("repos", __name__)


def _known_repo(owner, repo):
    resolver = current_app.config["STACK_RESOLVER"]
    for item in resolver.get_all_repos():
        if item.get("owner") == owner and item.get("repo") == repo:
            return True
    return False


def _refuse_unknown_repo(owner, repo):
    """Do not spend the GitHub token on a repo the loaded stacks do not name."""
    if _known_repo(owner, repo):
        return None
    return jsonify({"error": f"Repo {owner}/{repo} is not in the stack catalog"}), 403


@bp.route("/api/repos")
def list_repos():
    resolver = current_app.config["STACK_RESOLVER"]
    repos = resolver.get_all_repos()
    return jsonify({"items": repos})


@bp.route("/api/repos/<owner>/<repo>/branches")
def branches(owner, repo):
    refused = _refuse_unknown_repo(owner, repo)
    if refused is not None:
        return refused
    try:
        items = github_client.list_branches(owner, repo)
        return jsonify({"items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/repos/<owner>/<repo>/tags")
def tags(owner, repo):
    refused = _refuse_unknown_repo(owner, repo)
    if refused is not None:
        return refused
    try:
        items = github_client.list_tags(owner, repo)
        return jsonify({"items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/repos/<owner>/<repo>/commits")
def commits(owner, repo):
    refused = _refuse_unknown_repo(owner, repo)
    if refused is not None:
        return refused
    try:
        items = github_client.list_commits(owner, repo)
        return jsonify({"items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/repos/<owner>/<repo>/prs")
def repo_prs(owner, repo):
    refused = _refuse_unknown_repo(owner, repo)
    if refused is not None:
        return refused
    state = request.args.get("state", "open")
    if state not in ("open", "closed", "all"):
        state = "open"
    try:
        items = github_client.list_prs(owner, repo, state=state)
        return jsonify({"items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/prs")
def all_prs():
    state = request.args.get("state", "open")
    if state not in ("open", "closed", "all"):
        state = "open"
    resolver = current_app.config["STACK_RESOLVER"]
    repos = resolver.get_all_repos()
    try:
        items, queried, skipped = github_client.list_prs_all_repos(repos, state=state)
        return jsonify({"items": items, "reposQueried": queried, "reposSkipped": skipped})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
