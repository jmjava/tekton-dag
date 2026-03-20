from flask import Blueprint, current_app, jsonify, request

import k8s_client
import pipelinerun_builder as builder

bp = Blueprint("pipelines", __name__)


def _resolve_team(team_name):
    """Look up team and return (context, namespace) or abort 404."""
    registry = current_app.config["TEAM_REGISTRY"]
    team = registry.get_team(team_name)
    if not team:
        return None, None
    return registry.resolve_context(team_name)


def _summarize_run(pr):
    """Extract a summary dict from a raw PipelineRun resource."""
    cond = (pr.get("status", {}).get("conditions") or [{}])[0]
    start = pr.get("status", {}).get("startTime")
    end = pr.get("status", {}).get("completionTime")
    duration = None
    if start and end:
        from datetime import datetime, timezone
        s = datetime.fromisoformat(start.replace("Z", "+00:00"))
        e = datetime.fromisoformat(end.replace("Z", "+00:00"))
        duration = int((e - s).total_seconds())

    results = pr.get("status", {}).get("results") or pr.get("status", {}).get("pipelineResults") or []
    test_summary = next((r["value"] for r in results if r.get("name") == "test-summary"), None)

    params_list = pr.get("spec", {}).get("params") or []
    def param(name):
        return next((p["value"] for p in params_list if p.get("name") == name), None)

    return {
        "name": pr.get("metadata", {}).get("name"),
        "namespace": pr.get("metadata", {}).get("namespace"),
        "pipeline": (pr.get("spec", {}).get("pipelineRef") or {}).get("name", "-"),
        "status": cond.get("reason", "Unknown"),
        "message": cond.get("message"),
        "startTime": start,
        "completionTime": end,
        "durationSeconds": duration,
        "testSummary": test_summary,
        "prNumber": param("pr-number"),
        "changedApp": param("changed-app"),
    }


@bp.route("/api/teams/<team>/pipelineruns")
def list_runs(team):
    context, namespace = _resolve_team(team)
    if context is None:
        return jsonify({"error": f"Unknown team: {team}"}), 404
    limit = min(request.args.get("limit", 50, type=int), 100)
    items = k8s_client.list_pipelineruns(context, namespace, limit=limit)
    items.sort(key=lambda r: r.get("metadata", {}).get("creationTimestamp", ""), reverse=True)
    return jsonify({"items": [_summarize_run(r) for r in items]})


@bp.route("/api/teams/<team>/pipelineruns/<name>")
def get_run(team, name):
    context, namespace = _resolve_team(team)
    if context is None:
        return jsonify({"error": f"Unknown team: {team}"}), 404
    pr = k8s_client.get_pipelinerun(context, namespace, name)
    if not pr:
        return jsonify({"error": "PipelineRun not found"}), 404
    summary = _summarize_run(pr)
    summary["spec"] = pr.get("spec")
    summary["statusFull"] = pr.get("status")
    return jsonify(summary)


@bp.route("/api/teams/<team>/taskruns")
def list_team_taskruns(team):
    context, namespace = _resolve_team(team)
    if context is None:
        return jsonify({"error": f"Unknown team: {team}"}), 404
    pipelinerun = request.args.get("pipelineRun")
    items = k8s_client.list_taskruns(context, namespace, pipelinerun_name=pipelinerun)
    out = []
    for tr in items:
        cond = (tr.get("status", {}).get("conditions") or [{}])[0]
        out.append({
            "name": tr.get("metadata", {}).get("name"),
            "pipelineRun": tr.get("metadata", {}).get("labels", {}).get("tekton.dev/pipelineRun"),
            "task": (tr.get("spec", {}).get("taskRef") or {}).get("name"),
            "status": cond.get("reason"),
            "message": cond.get("message"),
            "startTime": tr.get("status", {}).get("startTime"),
            "completionTime": tr.get("status", {}).get("completionTime"),
        })
    return jsonify({"items": out})


@bp.route("/api/teams/<team>/trigger", methods=["POST"])
def trigger(team):
    context, namespace = _resolve_team(team)
    if context is None:
        return jsonify({"error": f"Unknown team: {team}"}), 404

    registry = current_app.config["TEAM_REGISTRY"]
    team_cfg = registry.get_team(team)
    data = request.get_json(force=True)

    pipeline_type = data.get("pipelineType")
    if pipeline_type not in ("pr", "bootstrap", "merge"):
        return jsonify({"error": "pipelineType must be pr, bootstrap, or merge"}), 400

    stack = data.get("stack")
    if not stack:
        return jsonify({"error": "stack is required"}), 400
    app_name = data.get("app")
    if not app_name and pipeline_type != "bootstrap":
        return jsonify({"error": "app is required"}), 400

    git_url = data.get("gitUrl", "https://github.com/jmjava/tekton-dag.git")
    git_revision = data.get("gitRevision", "main")
    image_registry = data.get("imageRegistry", team_cfg.get("imageRegistry", "localhost:5000"))

    try:
        if pipeline_type == "bootstrap":
            manifest = builder.build_bootstrap(
                git_url=git_url, git_revision=git_revision,
                stack_file=stack, image_registry=image_registry,
                namespace=namespace,
            )
        elif pipeline_type == "merge":
            manifest = builder.build_merge(
                stack_file=stack, changed_app=app_name,
                git_url=git_url, git_revision=git_revision,
                image_registry=image_registry, namespace=namespace,
            )
        else:
            pr_number = data.get("prNumber")
            if not pr_number:
                return jsonify({"error": "prNumber required for PR runs"}), 400
            manifest = builder.build_pr(
                stack_file=stack, changed_app=app_name,
                pr_number=pr_number,
                git_url=git_url, git_revision=git_revision,
                image_registry=image_registry, namespace=namespace,
                version_overrides=data.get("versionOverrides"),
                intercept_backend=data.get("interceptBackend",
                                           team_cfg.get("interceptBackend", "telepresence")),
                storage_class=data.get("storageClass", ""),
                build_images=data.get("buildImages", False),
            )
        name = k8s_client.create_pipelinerun(context, namespace, manifest)
        return jsonify({"ok": True, "pipelineRun": name, "namespace": namespace})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
