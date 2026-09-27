"""Canonical baggage / override-header contract.

The product rule: a request that targets an override container (PR pod)
carries one session value, usually ``x-dev-session: pr-42``. Every hop
must transfer **that original value** unchanged. Minting a new session
is only allowed at an originator when nothing incoming exists.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

from tekton_dag_common.stack_resolver_base import load_stack_yaml

DEFAULT_HEADER_NAME = "x-dev-session"
DEFAULT_BAGGAGE_KEY = "dev-session"
DEFAULT_ROLE = "forwarder"
ROLES = frozenset({"originator", "forwarder", "terminal"})

ENV_ENABLED = "BAGGAGE_ENABLED"
ENV_ROLE = "BAGGAGE_ROLE"
ENV_HEADER_NAME = "BAGGAGE_HEADER_NAME"
ENV_BAGGAGE_KEY = "BAGGAGE_KEY"
ENV_SESSION_VALUE = "BAGGAGE_SESSION_VALUE"
ENV_STRICT = "BAGGAGE_STRICT"


def _contract_dir() -> Path:
    here = Path(__file__).resolve()
    sibling = here.parents[2] / "baggage-contract"
    if sibling.is_dir():
        return sibling
    env = os.environ.get("TEKTON_DAG_BAGGAGE_CONTRACT")
    if env:
        return Path(env)
    return Path.cwd() / "libs" / "baggage-contract"


def load_contract() -> dict[str, Any]:
    path = _contract_dir() / "contract.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_vectors() -> dict[str, Any]:
    path = _contract_dir() / "vectors.json"
    return json.loads(path.read_text(encoding="utf-8"))


def first_nonblank(*values: str | None) -> str | None:
    for raw in values:
        if raw is None:
            continue
        text = str(raw).strip()
        if text:
            return text
    return None


def normalize_role(role: str | None) -> str | None:
    if role is None:
        return DEFAULT_ROLE
    text = str(role).strip().lower()
    if not text:
        return DEFAULT_ROLE
    if text in ROLES:
        return text
    return None


def incoming_session(
    role: str | None,
    header: str | None = None,
    cookie: str | None = None,
    query: str | None = None,
    session_value: str | None = None,
    *,
    enabled: bool = True,
) -> str | None:
    """Resolve the session to store for this request.

    Incoming header/cookie/query is the **original override**. It always
    wins. Originators mint ``session_value`` only when nothing arrived.
    """
    if not enabled:
        return None
    resolved = normalize_role(role)
    if resolved is None:
        return None
    incoming = first_nonblank(header, cookie, query)
    if resolved == "originator":
        return first_nonblank(incoming, session_value)
    return incoming


def outgoing_session(
    role: str | None,
    context_value: str | None = None,
    session_value: str | None = None,
) -> str | None:
    """Value to put on the next hop. Never invent a different override."""
    resolved = normalize_role(role)
    if resolved == "originator":
        return first_nonblank(context_value, session_value)
    if resolved == "forwarder":
        return first_nonblank(context_value)
    return None


def parse_baggage(header: str | None) -> dict[str, str]:
    entries: dict[str, str] = {}
    if not header or not str(header).strip():
        return entries
    for member in str(header).split(","):
        member = member.strip()
        if not member:
            continue
        eq = member.find("=")
        if eq < 1:
            continue
        entries[member[:eq].strip()] = member[eq + 1 :].strip()
    return entries


def serialize_baggage(entries: Mapping[str, str]) -> str:
    return ",".join(f"{k}={v}" for k, v in entries.items())


def merge_baggage(existing_header: str | None, key: str, value: str) -> str:
    entries = parse_baggage(existing_header)
    entries[key] = value
    return serialize_baggage(entries)


def apply_outgoing_headers(
    headers: dict[str, str] | None,
    *,
    role: str | None,
    context_value: str | None = None,
    session_value: str | None = None,
    header_name: str = DEFAULT_HEADER_NAME,
    baggage_key: str = DEFAULT_BAGGAGE_KEY,
) -> dict[str, str]:
    """Copy the original override onto outgoing headers. Does not rewrite it."""
    out = dict(headers or {})
    value = outgoing_session(role, context_value, session_value)
    if not value:
        return out
    out[header_name] = value
    existing = ""
    for key, current in list(out.items()):
        if key.lower() == "baggage":
            existing = current or ""
            break
    out["baggage"] = merge_baggage(existing, baggage_key, value)
    return out


def infer_role(app: Mapping[str, Any]) -> str:
    explicit = app.get("propagation-role") or app.get("propagationRole")
    if explicit:
        resolved = normalize_role(str(explicit))
        if resolved:
            return resolved
    downstream = app.get("downstream")
    if downstream is None or downstream == []:
        return "terminal"
    if str(app.get("role") or "").strip().lower() == "frontend":
        return "originator"
    return "forwarder"


def stack_propagation(stack: Mapping[str, Any]) -> dict[str, str]:
    prop = stack.get("propagation") if isinstance(stack.get("propagation"), dict) else {}
    return {
        "header_name": str(prop.get("header-name") or DEFAULT_HEADER_NAME),
        "baggage_key": str(prop.get("baggage-key") or DEFAULT_BAGGAGE_KEY),
        "strategy": str(prop.get("strategy") or "w3c-baggage"),
    }


def propagation_inject_enabled(stack: Mapping[str, Any]) -> bool:
    """Stack deploys inject library env unless propagation.enabled is false."""
    prop = stack.get("propagation") if isinstance(stack.get("propagation"), dict) else {}
    raw = prop.get("enabled", True)
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() not in {"false", "0", "no", "off"}


def first_downstream_name(app: Mapping[str, Any]) -> str | None:
    downstream = app.get("downstream")
    if not downstream:
        return None
    if isinstance(downstream, str):
        name = downstream.strip()
        return name or None
    if isinstance(downstream, list) and downstream:
        return str(downstream[0]).strip() or None
    return None


def app_config(stack: Mapping[str, Any], app: Mapping[str, Any]) -> dict[str, str]:
    prop = stack_propagation(stack)
    cfg = {
        "app": str(app.get("name") or ""),
        "role": infer_role(app),
        "header_name": prop["header_name"],
        "baggage_key": prop["baggage_key"],
        "enabled": "true" if propagation_inject_enabled(stack) else "false",
    }
    downstream = first_downstream_name(app)
    if downstream:
        cfg["downstream"] = downstream
        cfg["downstream_url"] = f"http://{downstream}"
    return cfg


def emit_env(config: Mapping[str, str], fmt: str = "env") -> str:
    role = config["role"]
    header = config["header_name"]
    key = config["baggage_key"]
    if fmt == "spring":
        return "\n".join(
            [
                "baggage.enabled=true",
                f"baggage.role={role.upper()}",
                f"baggage.header-name={header}",
                f"baggage.baggage-key={key}",
            ]
        )
    if fmt == "vite":
        return "\n".join(
            [
                "VITE_BAGGAGE_ENABLED=true",
                f"VITE_BAGGAGE_ROLE={role}",
                f"VITE_BAGGAGE_HEADER_NAME={header}",
                f"VITE_BAGGAGE_KEY={key}",
            ]
        )
    if fmt == "k8s":
        lines = [
            "- name: BAGGAGE_ENABLED",
            f'  value: "{config.get("enabled") or "true"}"',
            "- name: BAGGAGE_ROLE",
            f'  value: "{role}"',
            "- name: BAGGAGE_HEADER_NAME",
            f'  value: "{header}"',
            "- name: BAGGAGE_KEY",
            f'  value: "{key}"',
        ]
        if config.get("app"):
            lines.extend(["- name: APP_NAME", f'  value: "{config["app"]}"'])
        if config.get("downstream_url"):
            lines.extend(
                [
                    "- name: DOWNSTREAM_URL",
                    f'  value: "{config["downstream_url"]}"',
                    "- name: BFF_UPSTREAM",
                    f'  value: "{config["downstream_url"]}"',
                ]
            )
        return "\n".join(lines)
    prefix = "export " if fmt == "env" else ""
    return "\n".join(
        [
            f"{prefix}{ENV_ENABLED}=true",
            f"{prefix}{ENV_ROLE}={role}",
            f"{prefix}{ENV_HEADER_NAME}={header}",
            f"{prefix}{ENV_BAGGAGE_KEY}={key}",
        ]
    )


def find_app(stack: Mapping[str, Any], app_name: str) -> dict[str, Any] | None:
    for app in stack.get("apps") or []:
        if isinstance(app, dict) and str(app.get("name") or "") == app_name:
            return app
    return None


def doctor_stack(stack: Mapping[str, Any], *, stack_label: str = "stack") -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    apps = [a for a in (stack.get("apps") or []) if isinstance(a, dict)]
    if not stack.get("name"):
        errors.append(f"{stack_label}: missing name")
    if not apps:
        errors.append(f"{stack_label}: no apps")

    configs = [app_config(stack, app) for app in apps]
    originators = [c for c in configs if c["role"] == "originator"]
    if apps and not originators:
        warnings.append(f"{stack_label}: no originator after infer (header will not be minted)")
    if len(originators) > 1:
        names = ", ".join(c["app"] for c in originators)
        warnings.append(f"{stack_label}: multiple originators ({names})")

    for app, cfg in zip(apps, configs):
        explicit = app.get("propagation-role") or app.get("propagationRole")
        if explicit and normalize_role(str(explicit)) is None:
            errors.append(f"{cfg['app']}: invalid propagation-role {explicit!r}")
        if not app.get("name"):
            errors.append(f"{stack_label}: app missing name")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "apps": configs,
        "propagation": stack_propagation(stack),
    }


def _print_doctor(report: Mapping[str, Any]) -> int:
    prop = report["propagation"]
    print(f"header: {prop['header_name']}  baggage-key: {prop['baggage_key']}")
    print("apps:")
    for cfg in report["apps"]:
        print(f"  {cfg['app']}: role={cfg['role']} (preserve original {prop['header_name']} hop-to-hop)")
    for warning in report["warnings"]:
        print(f"WARN: {warning}", file=sys.stderr)
    for error in report["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if report["ok"] else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Baggage override-header contract tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    emit = sub.add_parser("emit", help="Emit library env from a stack app")
    emit.add_argument("--stack", required=True)
    emit.add_argument("--app")
    emit.add_argument("--all", action="store_true")
    emit.add_argument("--format", choices=("env", "dotenv", "vite", "spring", "k8s"), default="env")

    doc = sub.add_parser("doctor", help="Validate stack propagation roles")
    doc.add_argument("--stack", required=True)

    args = parser.parse_args(list(argv) if argv is not None else None)
    stack = load_stack_yaml(args.stack)
    if stack is None:
        print(f"ERROR: could not load stack {args.stack}", file=sys.stderr)
        return 1

    if args.cmd == "doctor":
        return _print_doctor(doctor_stack(stack, stack_label=args.stack))

    if args.all:
        chunks = []
        for app in stack.get("apps") or []:
            if not isinstance(app, dict):
                continue
            cfg = app_config(stack, app)
            chunks.append(f"# {cfg['app']}\n{emit_env(cfg, args.format)}")
        print("\n\n".join(chunks))
        return 0

    if not args.app:
        print("ERROR: --app or --all is required", file=sys.stderr)
        return 1
    app = find_app(stack, args.app)
    if app is None:
        print(f"ERROR: app {args.app!r} not in {args.stack}", file=sys.stderr)
        return 1
    print(emit_env(app_config(stack, app), args.format))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
