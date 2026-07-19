"""
Flask routes for the orchestration service.

Endpoints:
  POST /webhook/github   - GitHub webhook handler (PR opened/merged)
  POST /api/run          - Manual PipelineRun trigger
  POST /api/bootstrap    - Trigger bootstrap pipeline
  GET  /api/stacks       - List registered stacks
  GET  /api/runs         - List recent PipelineRuns
  GET  /api/apps/<app>/injection-status - Secrets/config injection status
  GET  /healthz          - Liveness probe
  GET  /readyz           - Readiness probe
"""

import json
import logging

from flask import Flask, request, jsonify, current_app

import k8s_client
import pipelinerun_builder as builder
import stackrun_builder
import graph_client
import webhook_auth
import registry_resolver

logger = logging.getLogger("orchestrator.routes")

try:
    from tekton_dag_common.deploy_injection import (
        injection_summary,
        validate_injection_refs,
    )
except ImportError:  # pragma: no cover
    injection_summary = None
    validate_injection_refs = None


def _reliability_kwargs(cfg, data=None):
    data = data or {}
    timeout = data.get("timeout", cfg.get("PIPELINE_TIMEOUT", "2h"))
    max_retries = data.get("max_retries", cfg.get("MAX_RETRIES", 2))
    try:
        max_retries = int(max_retries)
    except (TypeError, ValueError):
        max_retries = cfg.get("MAX_RETRIES", 2)
    return {"timeout": timeout, "max_retries": max_retries}


def _via_crd(cfg) -> bool:
    return bool(cfg.get("STACKRUN_VIA_CRD"))


def _create_run(cfg, *, mode: str, pipelinerun_manifest=None, stackrun_kwargs=None):
    """
    Create a PipelineRun or StackRun depending on STACKRUN_VIA_CRD.

    Returns (response_dict, status_code).
    """
    ns = cfg["NAMESPACE"]
    try:
        if _via_crd(cfg):
            manifest = stackrun_builder.build_stackrun(mode=mode, namespace=ns, **(stackrun_kwargs or {}))
            name = k8s_client.create_stackrun(manifest, namespace=ns)
            return {"status": "created", "stackrun": name, "pipelinerun": name, "mode": mode}, 200
        name = k8s_client.create_pipelinerun(pipelinerun_manifest, namespace=ns)
        return {"status": "created", "pipelinerun": name, "mode": mode}, 200
    except Exception as e:
        return {"error": str(e)}, 500


def _verify_webhook_or_reject():
    """Return a Flask response tuple when verification fails, else None."""
    cfg = current_app.config
    if not cfg.get("WEBHOOK_VERIFY_SIGNATURE", True):
        return None

    def _fetch(name, namespace="tekton-pipelines"):
        return k8s_client.get_secret_data(name, namespace=namespace)

    secret, status = webhook_auth.resolve_webhook_secret_status(
        configured_secret=cfg.get("WEBHOOK_SECRET", ""),
        secret_name=cfg.get("WEBHOOK_SECRET_NAME", ""),
        namespace=cfg.get("NAMESPACE", "tekton-pipelines"),
        fetch_secret=_fetch,
    )
    if status == webhook_auth.STATUS_UNSET:
        # No secret configured at all — allow for local/Kind without HMAC.
        logger.debug("Webhook signature not enforced: no secret configured")
        return None
    if status == webhook_auth.STATUS_MISSING:
        # Named Secret expected but absent/empty — fail closed in-cluster.
        logger.warning("Webhook rejected: secret %s missing or empty", cfg.get("WEBHOOK_SECRET_NAME"))
        return jsonify({"error": "webhook secret not found"}), 503
    if status == webhook_auth.STATUS_UNAVAILABLE:
        # No kubeconfig / API error — allow for unit tests & broken local kube;
        # operators should mount WEBHOOK_SECRET or ensure the Secret exists.
        logger.warning("Webhook signature not enforced: secret lookup unavailable")
        return None
    header = request.headers.get("X-Hub-Signature-256", "")
    if not webhook_auth.verify_signature(secret, request.get_data(), header):
        return jsonify({"error": "invalid webhook signature"}), 401
    return None


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
        cfg = current_app.config
        ns = cfg["NAMESPACE"]
        limit = request.args.get("limit", 20, type=int)
        summary = []
        if _via_crd(cfg):
            runs = k8s_client.list_stackruns(namespace=ns, limit=limit)
            for r in runs:
                status = r.get("status", {})
                summary.append({
                    "name": r["metadata"]["name"],
                    "pipeline": r.get("spec", {}).get("mode", ""),
                    "status": status.get("phase", "Unknown"),
                    "pipelinerun": status.get("pipelineRunName", ""),
                    "created": r["metadata"].get("creationTimestamp", ""),
                })
            return jsonify(summary)
        runs = k8s_client.list_pipelineruns(namespace=ns, limit=limit)
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
          "mode": "pr" | "bootstrap" | "merge" | "promote",
          "changed_app": "demo-fe",       (required for pr/merge)
          "pr_number": 42,                (required for pr)
          "stack_file": "stacks/...",     (optional, auto-resolved from changed_app)
          "intercept_backend": "...",     (optional)
          "git_revision": "main",         (optional)
          "release_version": "0.1.0",     (required for promote)
          "target_environment": "staging",(required for promote)
          "target_registry": "...",       (optional for promote)
          "timeout": "2h",                (optional)
          "max_retries": 2                (optional)
        }
        """
        data = request.get_json(force=True)
        mode = data.get("mode", "pr")
        cfg = current_app.config
        resolver = cfg["RESOLVER"]
        rel = _reliability_kwargs(cfg, data)

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
                **rel,
            )
            sr_kw = dict(
                stack_file=stack_file,
                git_url=git_url,
                git_revision=git_revision,
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                **rel,
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
                **rel,
            )
            sr_kw = dict(
                stack_file=stack_file,
                git_url=git_url,
                git_revision=git_revision,
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                changed_app=changed_app,
                **rel,
            )
        elif mode == "promote":
            release_version = data.get("release_version", "")
            target_environment = data.get("target_environment", "")
            changed_app = data.get("changed_app", "") or data.get("apps", "")
            if not release_version or not target_environment:
                return jsonify({
                    "error": "release_version and target_environment required for promote",
                }), 400
            if not changed_app:
                return jsonify({
                    "error": "changed_app (or apps) required for promote",
                }), 400
            require_approval = bool(data.get("require_approval", False))
            approved_by = data.get("approved_by", "")
            if require_approval and not approved_by:
                return jsonify({
                    "error": "approved_by required when require_approval is true",
                }), 400
            registries = registry_resolver.load_registries(cfg.get("REGISTRIES_FILE", ""))
            target = registry_resolver.resolve_promote_target(
                target_environment=target_environment,
                target_registry=data.get("target_registry", ""),
                credentials_secret=data.get("credentials_secret", ""),
                registries=registries,
            )
            run = builder.build_promote_pipelinerun(
                stack_file=stack_file,
                release_version=release_version,
                target_environment=target["target_environment"],
                image_registry=cfg["IMAGE_REGISTRY"],
                target_registry=target["target_registry"],
                credentials_secret=target["credentials_secret"],
                changed_app=changed_app,
                namespace=cfg["NAMESPACE"],
                require_approval=require_approval,
                approved_by=approved_by,
                **rel,
            )
            sr_kw = dict(
                stack_file=stack_file,
                image_registry=cfg["IMAGE_REGISTRY"],
                changed_app=changed_app,
                release_version=release_version,
                target_environment=target["target_environment"],
                target_registry=target["target_registry"],
                credentials_secret=target["credentials_secret"],
                require_approval=require_approval,
                approved_by=approved_by,
                **rel,
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
                **rel,
            )
            sr_kw = dict(
                stack_file=stack_file,
                git_url=git_url,
                git_revision=git_revision,
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                changed_app=changed_app,
                pr_number=pr_number,
                app_revisions=app_revisions,
                intercept_backend=intercept_backend,
                **rel,
            )

        body, code = _create_run(
            cfg, mode=mode, pipelinerun_manifest=run, stackrun_kwargs=sr_kw
        )
        return jsonify(body), code

    @app.route("/api/bootstrap", methods=["POST"])
    def bootstrap():
        """Trigger a bootstrap pipeline. Optional query: ?apps=app1,app2"""
        cfg = current_app.config
        data = request.get_json(silent=True) or {}
        stack_file = data.get("stack_file", cfg["STACK_FILE"])
        rel = _reliability_kwargs(cfg, data)

        run = builder.build_bootstrap_pipelinerun(
            git_url=cfg["GIT_URL"],
            git_revision=cfg["GIT_REVISION"],
            stack_file=stack_file,
            image_registry=cfg["IMAGE_REGISTRY"],
            cache_repo=cfg["CACHE_REPO"],
            namespace=cfg["NAMESPACE"],
            **rel,
        )
        sr_kw = dict(
            stack_file=stack_file,
            git_url=cfg["GIT_URL"],
            git_revision=cfg["GIT_REVISION"],
            image_registry=cfg["IMAGE_REGISTRY"],
            cache_repo=cfg["CACHE_REPO"],
            **rel,
        )
        body, code = _create_run(
            cfg, mode="bootstrap", pipelinerun_manifest=run, stackrun_kwargs=sr_kw
        )
        return jsonify(body), code

    @app.route("/webhook/github", methods=["POST"])
    def github_webhook():
        """
        GitHub webhook handler.
        Validates signature, parses PR event, resolves stack, creates PipelineRun.
        """
        rejected = _verify_webhook_or_reject()
        if rejected is not None:
            return rejected

        cfg = current_app.config
        resolver = cfg["RESOLVER"]
        rel = _reliability_kwargs(cfg)

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
            pr_repo_url = pr.get("base", {}).get("repo", {}).get("ssh_url", "")
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
                pr_repo_url=pr_repo_url,
                **rel,
            )
            sr_kw = dict(
                stack_file=stack_file,
                git_url=cfg["GIT_URL"],
                git_revision=cfg["GIT_REVISION"],
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                intercept_backend=cfg["INTERCEPT_BACKEND"],
                changed_app=changed_app,
                pr_number=pr_number,
                app_revisions=app_rev_json,
                pr_repo_url=pr_repo_url,
                **rel,
            )
            body, code = _create_run(
                cfg, mode="pr", pipelinerun_manifest=run, stackrun_kwargs=sr_kw
            )
            return jsonify(body), code

        elif action == "closed" and merged:
            run = builder.build_merge_pipelinerun(
                changed_app=changed_app,
                git_url=cfg["GIT_URL"],
                git_revision="main",
                stack_file=stack_file,
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                namespace=cfg["NAMESPACE"],
                **rel,
            )
            sr_kw = dict(
                stack_file=stack_file,
                git_url=cfg["GIT_URL"],
                git_revision="main",
                image_registry=cfg["IMAGE_REGISTRY"],
                cache_repo=cfg["CACHE_REPO"],
                changed_app=changed_app,
                **rel,
            )
            body, code = _create_run(
                cfg, mode="merge", pipelinerun_manifest=run, stackrun_kwargs=sr_kw
            )
            return jsonify(body), code

        return jsonify({"status": "ignored", "reason": f"action={action}"}), 200

    @app.route("/api/reload", methods=["POST"])
    def reload_stacks():
        """Reload stack and team configs from disk."""
        resolver = current_app.config["RESOLVER"]
        resolver.reload()
        return jsonify({"status": "reloaded", "stacks": len(resolver.list_stacks())})

    @app.route("/api/apps/<app_name>/injection-status", methods=["GET"])
    def app_injection_status(app_name):
        """
        Report secrets/config injection plan and whether referenced
        Secrets/ConfigMaps exist in the target namespace (M13).

        Uses StackResolver.find_app() so secrets/config blocks from stack YAML
        are preserved (list_stacks() only returns summary fields).
        """
        if injection_summary is None or validate_injection_refs is None:
            return jsonify({"error": "tekton_dag_common.deploy_injection unavailable"}), 501

        cfg = current_app.config
        resolver = cfg["RESOLVER"]
        ns = request.args.get("namespace", cfg["NAMESPACE"])

        found = None
        if hasattr(resolver, "find_app"):
            found = resolver.find_app(app_name)
        app = found.get("app") if isinstance(found, dict) else None
        if not isinstance(app, dict):
            return jsonify({"error": f"unknown app: {app_name}"}), 404

        summary = injection_summary(app)
        try:
            existing_secrets = k8s_client.list_secret_names(namespace=ns)
            existing_cms = k8s_client.list_configmap_names(namespace=ns)
        except Exception as exc:
            logger.error("injection-status k8s lookup failed: %s", exc)
            return jsonify({"error": f"kubernetes lookup failed: {exc}"}), 503
        errors = validate_injection_refs(
            app,
            existing_secrets=existing_secrets,
            existing_configmaps=existing_cms,
        )
        secret_status = {
            name: ("present" if name in existing_secrets else "missing")
            for name in summary["secrets"]
        }
        config_status = {
            name: ("present" if name in existing_cms else "missing")
            for name in summary["configmaps"]
        }
        return jsonify({
            "app": app_name,
            "namespace": ns,
            "stack_file": found.get("stack_file", ""),
            "ok": len(errors) == 0,
            "errors": errors,
            "secrets": secret_status,
            "configmaps": config_status,
            "injection": summary,
        })

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
