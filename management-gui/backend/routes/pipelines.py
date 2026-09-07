from flask import Blueprint, current_app, jsonify, request

import k8s_client
from tekton_dag_common.stackrun_builder import build_stackrun

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
        from datetime import datetime
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


def _summarize_stackrun(sr, pr=None):
    """Extract a summary dict from a StackRun, optionally enriched from its PipelineRun."""
    spec = sr.get("spec") or {}
    status = sr.get("status") or {}
    md = sr.get("metadata") or {}
    cond = (status.get("conditions") or [{}])[0]
    mode = spec.get("mode") or "-"
    summary = {
        "name": md.get("name"),
        "namespace": md.get("namespace"),
        "kind": "StackRun",
        "mode": mode,
        "pipeline": mode,
        "stackRef": spec.get("stackRef") or "",
        "stackFile": spec.get("stackFile") or "",
        "changedApp": spec.get("changedApp"),
        "prNumber": spec.get("prNumber") or (md.get("annotations") or {}).get("tektondag.io/pr-number"),
        "pipelineRunName": status.get("pipelineRunName") or "",
        "status": status.get("phase") or cond.get("reason") or "Unknown",
        "message": cond.get("message"),
        "startTime": md.get("creationTimestamp"),
        "completionTime": None,
        "durationSeconds": None,
        "testSummary": None,
        "requireApproval": bool(spec.get("requireApproval")),
        "approvedBy": spec.get("approvedBy") or "",
        "releaseVersion": spec.get("releaseVersion") or "",
        "targetEnvironment": spec.get("targetEnvironment") or "",
    }
    if pr:
        prs = _summarize_run(pr)
        summary["pipeline"] = prs.get("pipeline") or mode
        summary["startTime"] = prs.get("startTime") or summary["startTime"]
        summary["completionTime"] = prs.get("completionTime")
        summary["durationSeconds"] = prs.get("durationSeconds")
        summary["testSummary"] = prs.get("testSummary")
        if prs.get("status") and summary["status"] in ("Pending", "Unknown", ""):
            summary["status"] = prs["status"]
    return summary


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


@bp.route("/api/teams/<team>/stackruns")
def list_stackruns(team):
    context, namespace = _resolve_team(team)
    if context is None:
        return jsonify({"error": f"Unknown team: {team}"}), 404
    limit = min(request.args.get("limit", 50, type=int), 100)
    items = k8s_client.list_stackruns(context, namespace, limit=limit)
    items.sort(key=lambda r: r.get("metadata", {}).get("creationTimestamp", ""), reverse=True)
    return jsonify({"items": [_summarize_stackrun(r) for r in items]})


@bp.route("/api/teams/<team>/stackruns/<name>")
def get_stackrun(team, name):
    context, namespace = _resolve_team(team)
    if context is None:
        return jsonify({"error": f"Unknown team: {team}"}), 404
    sr = k8s_client.get_stackrun(context, namespace, name)
    if not sr:
        return jsonify({"error": "StackRun not found"}), 404
    pr = None
    pr_name = (sr.get("status") or {}).get("pipelineRunName")
    if pr_name:
        pr_ns = (sr.get("spec") or {}).get("pipelineNamespace") or namespace
        pr = k8s_client.get_pipelinerun(context, pr_ns, pr_name)
    summary = _summarize_stackrun(sr, pr)
    summary["spec"] = sr.get("spec")
    summary["statusFull"] = sr.get("status")
    return jsonify(summary)


@bp.route("/api/teams/<team>/stackruns/<name>", methods=["PATCH"])
def patch_stackrun(team, name):
    context, namespace = _resolve_team(team)
    if context is None:
        return jsonify({"error": f"Unknown team: {team}"}), 404
    data = request.get_json(force=True) or {}
    approved_by = str(data.get("approvedBy") or "").strip()
    if not approved_by:
        return jsonify({"error": "approvedBy is required"}), 400
    if k8s_client.get_stackrun(context, namespace, name) is None:
        return jsonify({"error": "StackRun not found"}), 404
    try:
        sr = k8s_client.patch_stackrun(
            context, namespace, name, {"spec": {"approvedBy": approved_by}}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(_summarize_stackrun(sr))


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
    if pipeline_type not in ("pr", "bootstrap", "merge", "promote"):
        return jsonify({"error": "pipelineType must be pr, bootstrap, merge, or promote"}), 400

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
        mode = pipeline_type
        sr_kw = dict(
            mode=mode,
            namespace=namespace,
            stack_file=stack,
            git_url=git_url,
            git_revision=git_revision,
            image_registry=image_registry,
        )
        if pipeline_type == "merge":
            sr_kw["changed_app"] = app_name
        elif pipeline_type == "pr":
            pr_number = data.get("prNumber")
            if not pr_number:
                return jsonify({"error": "prNumber required for PR runs"}), 400
            sr_kw["changed_app"] = app_name
            sr_kw["pr_number"] = pr_number
            sr_kw["intercept_backend"] = data.get(
                "interceptBackend", team_cfg.get("interceptBackend", "telepresence")
            )
        elif pipeline_type == "promote":
            release_version = data.get("releaseVersion")
            target_environment = data.get("targetEnvironment")
            if not release_version or not target_environment:
                return jsonify({"error": "releaseVersion and targetEnvironment required for promote"}), 400
            sr_kw["changed_app"] = app_name
            sr_kw["release_version"] = release_version
            sr_kw["target_environment"] = target_environment
            sr_kw["target_registry"] = data.get("targetRegistry") or image_registry
            sr_kw["require_approval"] = bool(data.get("requireApproval", True))
            if data.get("approvedBy"):
                sr_kw["approved_by"] = data["approvedBy"]
        name = k8s_client.create_stackrun(context, namespace, build_stackrun(**sr_kw))
        return jsonify({"ok": True, "pipelineRun": name, "stackrun": name, "namespace": namespace})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
