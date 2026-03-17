"""
Flask routes for the orchestration service.

Endpoints:
  POST /webhook/github   - GitHub webhook handler (PR opened/merged)
  POST /api/run          - Manual PipelineRun trigger
  POST /api/bootstrap    - Trigger bootstrap pipeline
  GET  /api/stacks       - List registered stacks
  GET  /api/runs         - List recent PipelineRuns
  GET  /healthz          - Liveness probe
  GET  /readyz           - Readiness probe
"""

import hashlib
import hmac
import json
import logging

from flask import Flask, request, jsonify, current_app

import k8s_client
import pipelinerun_builder as builder
import graph_client

logger = logging.getLogger("orchestrator.routes")


def register_routes(app: Flask):
    @app.route("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    @app.route("/readyz")
    def readyz():
        resolver = current_app.config["RESOLVER"]
        stacks = resolver.list_stacks()
        return jsonify({"status": "ok", "stacks_loaded": len(stacks)})

    @app.route("/api/stacks", methods=["GET"])
    def list_stacks():
        resolver = current_app.config["RESOLVER"]
        return jsonify(resolver.list_stacks())

    @app.route("/api/teams", methods=["GET"])
    def list_teams():
        resolver = current_app.config["RESOLVER"]
        return jsonify(resolver.list_teams())

    @app.route("/api/runs", methods=["GET"])
    def list_runs():
        ns = current_app.config["NAMESPACE"]
        limit = request.args.get("limit", 20, type=int)
        runs = k8s_client.list_pipelineruns(namespace=ns, limit=limit)
        summary = []
        for r in runs:
            conditions = r.get("status", {}).get("conditions", [{}])
            reason = conditions[0].get("reason", "Unknown") if conditions else "Unknown"
            summary.append({
                "name": r["metadata"]["name"],
                "pipeline": r["metadata"].get("labels", {}).get("tekton.dev/pipeline", ""),
                "status": reason,
                "created": r["metadata"].get("creationTimestamp", ""),
            })
        return jsonify(summary)

    @app.route("/api/run", methods=["POST"])
    def manual_run():
        """
        Manual trigger. JSON body:
        {
          "mode": "pr" | "bootstrap" | "merge",
          "changed_app": "demo-fe",       (required for pr/merge)
          "pr_number": 42,                (required for pr)
          "stack_file": "stacks/...",     (optional, auto-resolved from changed_app)
          "intercept_backend": "...",     (optional)
          "git_revision": "main"          (optional)
        }
        """
        data = request.get_json(force=True)
        mode = data.get("mode", "pr")
        cfg = current_app.config
        resolver = cfg["RESOLVER"]

        stack_file = data.get("stack_file", cfg["STACK_FILE"])
        git_url = data.get("git_url", cfg["GIT_URL"])
        git_revision = data.get("git_revision", cfg["GIT_REVISION"])
        intercept_backend = data.get("intercept_backend", cfg["INTERCEPT_BACKEND"])

        if mode == "bootstrap":
            run = builder.build_bootstrap_pipelinerun(
                git_url=git_url,
                git_revision=git_revision,
                stack_file=stack_file,
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                namespace=cfg["NAMESPACE"],
            )
        elif mode == "merge":
            changed_app = data.get("changed_app", "")
            if not changed_app:
                return jsonify({"error": "changed_app required for merge"}), 400
            run = builder.build_merge_pipelinerun(
                changed_app=changed_app,
                git_url=git_url,
                git_revision=git_revision,
                stack_file=stack_file,
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                namespace=cfg["NAMESPACE"],
            )
        else:
            changed_app = data.get("changed_app", "")
            pr_number = data.get("pr_number", 0)
            if not changed_app or not pr_number:
                return jsonify({"error": "changed_app and pr_number required for pr"}), 400
            app_revisions = data.get("app_revisions", "{}")
            run = builder.build_pr_pipelinerun(
                stack_file=stack_file,
                changed_app=changed_app,
                pr_number=pr_number,
                git_url=git_url,
                git_revision=git_revision,
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                intercept_backend=intercept_backend,
                app_revisions=app_revisions,
                namespace=cfg["NAMESPACE"],
            )

        try:
            name = k8s_client.create_pipelinerun(run, namespace=cfg["NAMESPACE"])
            return jsonify({"status": "created", "pipelinerun": name, "mode": mode})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/bootstrap", methods=["POST"])
    def bootstrap():
        """Trigger a bootstrap pipeline. Optional query: ?apps=app1,app2"""
        cfg = current_app.config
        data = request.get_json(silent=True) or {}
        stack_file = data.get("stack_file", cfg["STACK_FILE"])

        run = builder.build_bootstrap_pipelinerun(
            git_url=cfg["GIT_URL"],
            git_revision=cfg["GIT_REVISION"],
            stack_file=stack_file,
            image_registry=cfg["IMAGE_REGISTRY"],
            cache_repo=cfg["CACHE_REPO"],
            namespace=cfg["NAMESPACE"],
        )

        try:
            name = k8s_client.create_pipelinerun(run, namespace=cfg["NAMESPACE"])
            return jsonify({"status": "created", "pipelinerun": name, "mode": "bootstrap"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/webhook/github", methods=["POST"])
    def github_webhook():
        """
        GitHub webhook handler.
        Validates signature, parses PR event, resolves stack, creates PipelineRun.
        """
        cfg = current_app.config
        resolver = cfg["RESOLVER"]

        event = request.headers.get("X-GitHub-Event", "")
        if event != "pull_request":
            return jsonify({"status": "ignored", "reason": f"event={event}"}), 200

        payload = request.get_json(force=True)
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})
        repo_name = pr.get("base", {}).get("repo", {}).get("name", "")
        head_sha = pr.get("head", {}).get("sha", "")
        pr_number = payload.get("number", 0)
        merged = pr.get("merged", False)

        logger.info(
            "Webhook: event=%s action=%s repo=%s pr=%s",
            event, action, repo_name, pr_number,
        )

        resolved = resolver.resolve_repo(repo_name)
        if not resolved:
            logger.warning("No stack mapping for repo: %s", repo_name)
            return jsonify({"status": "ignored", "reason": f"unknown repo: {repo_name}"}), 200

        stack_file = resolved["stack_file"]
        changed_app = resolved["app_name"]

        if action in ("opened", "synchronize", "reopened"):
            app_rev_json = json.dumps({changed_app: head_sha})
            run = builder.build_pr_pipelinerun(
                stack_file=stack_file,
                changed_app=changed_app,
                pr_number=pr_number,
                git_url=cfg["GIT_URL"],
                git_revision=cfg["GIT_REVISION"],
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                intercept_backend=cfg["INTERCEPT_BACKEND"],
                app_revisions=app_rev_json,
                namespace=cfg["NAMESPACE"],
                pr_repo_url=pr.get("base", {}).get("repo", {}).get("ssh_url", ""),
            )
            try:
                name = k8s_client.create_pipelinerun(run, namespace=cfg["NAMESPACE"])
                return jsonify({"status": "created", "pipelinerun": name, "mode": "pr"})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        elif action == "closed" and merged:
            run = builder.build_merge_pipelinerun(
                changed_app=changed_app,
                git_url=cfg["GIT_URL"],
                git_revision="main",
                stack_file=stack_file,
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                namespace=cfg["NAMESPACE"],
            )
            try:
                name = k8s_client.create_pipelinerun(run, namespace=cfg["NAMESPACE"])
                return jsonify({"status": "created", "pipelinerun": name, "mode": "merge"})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        return jsonify({"status": "ignored", "reason": f"action={action}"}), 200

    @app.route("/api/reload", methods=["POST"])
    def reload_stacks():
        """Reload stack and team configs from disk."""
        resolver = current_app.config["RESOLVER"]
        resolver.reload()
        return jsonify({"status": "reloaded", "stacks": len(resolver.list_stacks())})

    @app.route("/api/test-plan", methods=["GET"])
    def test_plan():
        """
        Query the minimal test set for a changed app.
        Query params: app (required), radius (optional, default 1).
        """
        app_name = request.args.get("app", "")
        if not app_name:
            return jsonify({"error": "app parameter required"}), 400
        radius = request.args.get("radius", 1, type=int)
        try:
            plan = graph_client.query_test_plan(app_name, radius=radius)
            return jsonify(plan)
        except Exception as e:
            logger.error("test-plan query failed: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/graph/ingest", methods=["POST"])
    def graph_ingest():
        """
        Ingest trace data into the graph.
        Body: {"fixture_file": "path/to/file.json"} or {"traces": [...]}.
        """
        data = request.get_json(force=True)
        try:
            if "fixture_file" in data:
                count = graph_client.ingest_from_file(data["fixture_file"])
                return jsonify({"status": "ingested", "traces": count})
            elif "traces" in data:
                graph_client.clear_graph()
                graph_client.create_constraints()
                graph_client.ingest_traces(data["traces"])
                return jsonify({"status": "ingested", "traces": len(data["traces"])})
            else:
                return jsonify({"error": "provide fixture_file or traces"}), 400
        except Exception as e:
            logger.error("graph ingest failed: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/graph/stats", methods=["GET"])
    def graph_stats():
        """Return graph statistics (node/edge counts)."""
        try:
            stats = graph_client.graph_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error("graph stats failed: %s", e)
            return jsonify({"error": str(e)}), 500
