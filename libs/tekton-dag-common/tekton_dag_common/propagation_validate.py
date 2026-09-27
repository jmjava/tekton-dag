"""Fail-closed hop-to-hop validation for the original override header.

A PR (or other override) deploys one container somewhere in the stack.
Intercepts match only traffic that still carries that original session
(usually ``x-dev-session: pr-42``). If any hop drops or rewrites the
value, the override pod never sees the match.

Sample apps should echo a hop report so this check is exact::

    {"app": "demo-fe", "session": "pr-42", "hops": [{...}]}

Unstructured bodies still fail if the original value is missing when a
header is required, or if a hop up to the deepest intercept is absent.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from tekton_dag_common.baggage_contract import (
    DEFAULT_HEADER_NAME,
    apply_outgoing_headers,
    incoming_session,
    infer_role,
    load_stack_yaml,
    outgoing_session,
    stack_propagation,
)

APP_KEYS = ("app", "name", "service")
SESSION_KEYS = ("session", "devSession", "dev_session", "headerValue", "header_value")
NESTED_KEYS = ("hops", "downstream", "downstreamHops", "calls", "children")


@dataclass
class HopCheck:
    app: str
    role: str
    intercepted: bool
    required: bool
    reached: bool
    session: str | None
    status: str
    detail: str


@dataclass
class ValidationReport:
    ok: bool
    header_name: str
    header_value: str
    header_found: bool
    rewritten: bool
    failures: list[str] = field(default_factory=list)
    hops: list[HopCheck] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "header_name": self.header_name,
            "header_value": self.header_value,
            "header_found": self.header_found,
            "rewritten": self.rewritten,
            "failures": list(self.failures),
            "hops": [asdict(h) for h in self.hops],
        }


def split_names(raw: str | Iterable[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [part for part in raw.replace(",", " ").split() if part]
    return [str(part) for part in raw if str(part).strip()]


def deepest_intercept_index(chain: list[str], build_apps: list[str]) -> int:
    """1-based index of the last intercepted app, or 0 if none."""
    deepest = 0
    intercepted = set(build_apps)
    for i, app in enumerate(chain, start=1):
        if app in intercepted:
            deepest = i
    return deepest


def header_required_at(index: int, deepest: int) -> bool:
    """Header must reach this hop (1-based) unless it is past the last intercept."""
    if deepest <= 0:
        return True
    return index <= deepest


def _as_mapping(value: Any) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def parse_response(body: Any) -> tuple[Any, str]:
    """Return (parsed JSON or None, raw text)."""
    if isinstance(body, (dict, list)):
        return body, json.dumps(body)
    text = "" if body is None else str(body)
    stripped = text.strip()
    if not stripped:
        return None, text
    try:
        return json.loads(stripped), text
    except json.JSONDecodeError:
        return None, text


def _session_from_obj(obj: Mapping[str, Any], header_name: str) -> str | None:
    for key in SESSION_KEYS:
        if key in obj and obj[key] not in (None, ""):
            return str(obj[key]).strip()
    if header_name in obj and obj[header_name] not in (None, ""):
        return str(obj[header_name]).strip()
    lower = header_name.lower()
    for key, value in obj.items():
        if str(key).lower() == lower and value not in (None, ""):
            return str(value).strip()
    return None


def _app_from_obj(obj: Mapping[str, Any]) -> str | None:
    for key in APP_KEYS:
        if key in obj and obj[key] not in (None, ""):
            return str(obj[key]).strip()
    return None


def collect_hop_reports(
    parsed: Any,
    header_name: str = DEFAULT_HEADER_NAME,
) -> list[dict[str, str | None]]:
    """Walk a hop-report tree and return ``[{app, session}, ...]``."""
    found: list[dict[str, str | None]] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        obj = _as_mapping(node)
        if obj is None:
            return
        app = _app_from_obj(obj)
        session = _session_from_obj(obj, header_name)
        if app or session:
            found.append({"app": app, "session": session})
        for key in NESTED_KEYS:
            if key in obj:
                walk(obj[key])
        for key, value in obj.items():
            if key in NESTED_KEYS or key in APP_KEYS or key in SESSION_KEYS:
                continue
            if isinstance(value, (dict, list)):
                walk(value)

    walk(parsed)
    return found


def collect_sessions(
    parsed: Any,
    header_name: str = DEFAULT_HEADER_NAME,
) -> list[str]:
    return [
        str(item["session"])
        for item in collect_hop_reports(parsed, header_name)
        if item.get("session")
    ]


def text_contains(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    return needle.lower() in haystack.lower()


def is_unreachable(text: str, parsed: Any) -> bool:
    if parsed == {"error": "unreachable"}:
        return True
    lowered = text.lower()
    return '"error":"unreachable"' in lowered.replace(" ", "") or "unreachable" in lowered


def aliases_from_stack(stack: Mapping[str, Any]) -> dict[str, list[str]]:
    """Stack app name plus repo basename (sample apps often echo the repo)."""
    aliases: dict[str, list[str]] = {}
    for app in stack.get("apps") or []:
        if not isinstance(app, dict) or not app.get("name"):
            continue
        name = str(app["name"])
        extras = [name]
        repo = str(app.get("repo") or "")
        if "/" in repo:
            extras.append(repo.rsplit("/", 1)[-1])
        elif repo:
            extras.append(repo)
        aliases[name] = extras
    return aliases


def _name_matches(needle: str, candidates: Iterable[str]) -> bool:
    lowered = needle.lower()
    return any(lowered in str(c).lower() or str(c).lower() in lowered for c in candidates)


def evaluate_propagation(
    body: Any,
    *,
    chain: Iterable[str] | str,
    header_value: str,
    build_apps: Iterable[str] | str | None = None,
    header_name: str = DEFAULT_HEADER_NAME,
    roles: Mapping[str, str] | None = None,
    aliases: Mapping[str, Iterable[str]] | None = None,
    single_app_health_only: bool | None = None,
) -> ValidationReport:
    """Fail-closed check that the original override survived the chain."""
    apps = split_names(chain)
    intercepted = split_names(build_apps)
    deepest = deepest_intercept_index(apps, intercepted)
    parsed, text = parse_response(body)
    reports = collect_hop_reports(parsed, header_name) if parsed is not None else []
    sessions = [str(item["session"]) for item in reports if item.get("session")]
    role_map = {str(k): str(v) for k, v in (roles or {}).items()}

    header_value = (header_value or "").strip()
    header_found = bool(header_value) and (
        header_value in sessions or header_value in text
    )
    rewritten_values = [s for s in sessions if s != header_value]
    rewritten = bool(header_value) and bool(rewritten_values)

    health_only = (
        len(apps) <= 1 if single_app_health_only is None else single_app_health_only
    )
    failures: list[str] = []
    hops: list[HopCheck] = []

    if not health_only and is_unreachable(text, parsed):
        failures.append("originator unreachable — cannot prove hop-to-hop copy")

    if rewritten:
        seen = ", ".join(sorted(set(rewritten_values)))
        failures.append(
            f"original override {header_value!r} was rewritten to {seen}"
        )

    need_header = bool(header_value) and not health_only
    if need_header and not header_found:
        failures.append(
            f"original override {header_value!r} missing from response"
        )

    alias_map = {str(k): [str(x) for x in v] for k, v in (aliases or {}).items()}

    for index, app in enumerate(apps, start=1):
        required = header_required_at(index, deepest)
        is_intercepted = app in intercepted
        role = role_map.get(app, "unknown")
        names = alias_map.get(app) or [app]
        matched = [
            item
            for item in reports
            if item.get("app") and _name_matches(str(item["app"]), names)
        ]
        session = next((item.get("session") for item in matched if item.get("session")), None)
        reached = bool(matched) or any(text_contains(text, name) for name in names)
        if session is None and header_value and header_value in text and reached:
            session = header_value

        if health_only:
            status = "OK"
            detail = "single-app health check — hop assertion skipped"
        elif not required:
            status = "OK"
            detail = "beyond deepest intercept — header not required"
        elif not reached:
            status = "FAIL"
            detail = "NOT REACHED (header required at this hop)"
            failures.append(f"{app}: not reached")
        elif header_value and session and session != header_value:
            status = "FAIL"
            detail = f"REWRITTEN session={session!r} (expected {header_value!r})"
            failures.append(f"{app}: rewritten {session!r}")
        elif header_value and required and not session and not header_found:
            status = "FAIL"
            detail = f"original override {header_value!r} not confirmed"
            failures.append(f"{app}: original override not confirmed")
        else:
            status = "PASS"
            detail = f"REACHED session={session or header_value!r}"

        hops.append(
            HopCheck(
                app=app,
                role=role,
                intercepted=is_intercepted,
                required=required,
                reached=reached,
                session=session,
                status=status,
                detail=detail,
            )
        )

    unique_failures = list(dict.fromkeys(failures))
    return ValidationReport(
        ok=not unique_failures,
        header_name=header_name,
        header_value=header_value,
        header_found=header_found,
        rewritten=rewritten,
        failures=unique_failures,
        hops=hops,
    )


def simulate_chain(
    apps: Iterable[Mapping[str, Any]],
    *,
    incoming_header: str,
    header_name: str = DEFAULT_HEADER_NAME,
    baggage_key: str = "dev-session",
    mint_value: str | None = None,
) -> dict[str, Any]:
    """In-process hop-to-hop copy using the contract. Used by unit tests."""
    incoming: str | None = incoming_header
    hops: list[dict[str, Any]] = []
    outgoing_headers: dict[str, str] = {}
    for app in apps:
        role = infer_role(app)
        name = str(app.get("name") or "")
        context = incoming_session(
            role,
            incoming,
            session_value=mint_value if role == "originator" else None,
            enabled=True,
        )
        outgoing_headers = apply_outgoing_headers(
            {},
            role=role,
            context_value=context,
            session_value=mint_value if role == "originator" else None,
            header_name=header_name,
            baggage_key=baggage_key,
        )
        hops.append(
            {
                "app": name,
                "role": role,
                "session": context,
                "outgoing": outgoing_session(role, context, mint_value if role == "originator" else None),
            }
        )
        incoming = outgoing_headers.get(header_name)
    tree: dict[str, Any] | None = None
    for hop in reversed(hops):
        node = {"app": hop["app"], "session": hop["session"], "hops": [tree] if tree else []}
        tree = node
    return {
        "hops": hops,
        "report": tree,
        "final_outgoing": outgoing_headers,
    }


def _roles_from_stack(stack: Mapping[str, Any]) -> dict[str, str]:
    roles: dict[str, str] = {}
    for app in stack.get("apps") or []:
        if isinstance(app, dict) and app.get("name"):
            roles[str(app["name"])] = infer_role(app)
    return roles


def format_report(report: ValidationReport) -> str:
    lines = [
        "Hop-by-hop verification (fail-closed):",
        f"  original override: {report.header_name}={report.header_value}",
        f"  found: {report.header_found}  rewritten: {report.rewritten}",
    ]
    for hop in report.hops:
        marker = " [INTERCEPTED]" if hop.intercepted else ""
        lines.append(
            f"  HOP {hop.app} ({hop.role}){marker}: {hop.status} — {hop.detail}"
        )
    if report.failures:
        lines.append("")
        for failure in report.failures:
            lines.append(f"FAIL: {failure}")
    else:
        lines.append("")
        lines.append("PASS: original override transferred hop-to-hop")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed hop-to-hop override-header validation"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    ev = sub.add_parser("evaluate", help="Evaluate a hop-report response")
    ev.add_argument("--response", required=True, help="Response body, or - for stdin")
    ev.add_argument("--chain", required=True, help="Space-separated apps")
    ev.add_argument("--header-val", default="")
    ev.add_argument("--header-name", default=DEFAULT_HEADER_NAME)
    ev.add_argument("--build-apps", default="")
    ev.add_argument("--stack", help="Optional stack YAML for roles")

    sim = sub.add_parser("simulate", help="Simulate contract copy along a stack chain")
    sim.add_argument("--stack", required=True)
    sim.add_argument("--header-val", default="pr-42")
    sim.add_argument("--chain", help="Override chain (default: stack app order)")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "simulate":
        stack = load_stack_yaml(args.stack)
        if stack is None:
            print(f"ERROR: could not load stack {args.stack}", file=sys.stderr)
            return 1
        apps = [a for a in (stack.get("apps") or []) if isinstance(a, dict)]
        if args.chain:
            wanted = split_names(args.chain)
            by_name = {str(a.get("name")): a for a in apps}
            apps = [by_name[n] for n in wanted if n in by_name]
        prop = stack_propagation(stack)
        simulated = simulate_chain(
            apps,
            incoming_header=args.header_val,
            header_name=prop["header_name"],
            baggage_key=prop["baggage_key"],
        )
        print(json.dumps(simulated, indent=2))
        values = [h["session"] for h in simulated["hops"] if h["session"]]
        if values and any(v != args.header_val for v in values):
            print("FAIL: simulation rewrote the original override", file=sys.stderr)
            return 1
        return 0

    raw = args.response
    if raw == "-":
        body = sys.stdin.read()
    else:
        body = raw
    roles = None
    aliases = None
    if args.stack:
        stack = load_stack_yaml(args.stack)
        if stack is not None:
            roles = _roles_from_stack(stack)
            aliases = aliases_from_stack(stack)
            prop = stack_propagation(stack)
            if args.header_name == DEFAULT_HEADER_NAME:
                args.header_name = prop["header_name"]
    report = evaluate_propagation(
        body,
        chain=args.chain,
        header_value=args.header_val,
        build_apps=args.build_apps,
        header_name=args.header_name,
        roles=roles,
        aliases=aliases,
    )
    print(format_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
