"""
Role-aware W3C baggage / x-dev-session middleware for Flask.

Invariant: the original override header (the session that selects a PR
container somewhere in the stack) is transferred unchanged hop-to-hop.
Originators adopt an incoming value when present and mint only as fallback.

Call ``install(app)``. Do not write your own header forwarding.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from flask import g, request
import requests as _requests

DEFAULT_HEADER_NAME = "x-dev-session"
DEFAULT_BAGGAGE_KEY = "dev-session"
ROLES = frozenset({"originator", "forwarder", "terminal"})

_installed_requests = False
_original_request = None


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def first_nonblank(*values):
    for raw in values:
        if raw is None:
            continue
        text = str(raw).strip()
        if text:
            return text
    return None


def normalize_role(role):
    if role is None:
        return "forwarder"
    text = str(role).strip().lower()
    if not text:
        return "forwarder"
    return text if text in ROLES else None


def incoming_session(role, header=None, cookie=None, query=None, session_value=None, *, enabled=True):
    if not enabled:
        return None
    resolved = normalize_role(role)
    if resolved is None:
        return None
    incoming = first_nonblank(header, cookie, query)
    if resolved == "originator":
        return first_nonblank(incoming, session_value)
    return incoming


def outgoing_session(role, context_value=None, session_value=None):
    resolved = normalize_role(role)
    if resolved == "originator":
        return first_nonblank(context_value, session_value)
    if resolved == "forwarder":
        return first_nonblank(context_value)
    return None


@dataclass(frozen=True)
class BaggageConfig:
    enabled: bool
    role: str | None
    header_name: str
    baggage_key: str
    session_value: str

    @classmethod
    def from_env(cls) -> "BaggageConfig":
        return cls(
            enabled=_env("BAGGAGE_ENABLED", "").lower() == "true",
            role=normalize_role(_env("BAGGAGE_ROLE", "forwarder")),
            header_name=_env("BAGGAGE_HEADER_NAME", DEFAULT_HEADER_NAME) or DEFAULT_HEADER_NAME,
            baggage_key=_env("BAGGAGE_KEY", DEFAULT_BAGGAGE_KEY) or DEFAULT_BAGGAGE_KEY,
            session_value=_env("BAGGAGE_SESSION_VALUE", ""),
        )


def __getattr__(name: str):
    cfg = BaggageConfig.from_env()
    mapping = {
        "HEADER_NAME": cfg.header_name,
        "BAGGAGE_KEY": cfg.baggage_key,
        "SESSION_VALUE": cfg.session_value,
        "ROLE": cfg.role or "",
    }
    if name in mapping:
        return mapping[name]
    raise AttributeError(name)


def parse_baggage(header):
    entries = {}
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


def merge_baggage(existing_header, key, value):
    entries = parse_baggage(existing_header)
    entries[key] = value
    return serialize_baggage(entries)


def serialize_baggage(entries):
    return ",".join(f"{k}={v}" for k, v in entries.items())


def _current_context():
    try:
        return getattr(g, "dev_session", None)
    except RuntimeError:
        return None


def _attach_headers(headers, cfg: BaggageConfig, value: str):
    if headers is None:
        headers = {}
    if isinstance(headers, dict):
        out = dict(headers)
        out[cfg.header_name] = value
        existing = ""
        for key, current in out.items():
            if str(key).lower() == "baggage":
                existing = current or ""
                break
        out["baggage"] = merge_baggage(existing, cfg.baggage_key, value)
        return out
    try:
        headers[cfg.header_name] = value
        existing = headers.get("baggage", "")
        headers["baggage"] = merge_baggage(existing, cfg.baggage_key, value)
    except Exception:
        pass
    return headers


def install_requests():
    """Instrument requests.Session so apps do not wrap clients themselves."""
    global _installed_requests, _original_request
    if _installed_requests:
        return
    _original_request = _requests.Session.request

    def wrapped(self, method, url, **kwargs):
        cfg = BaggageConfig.from_env()
        if cfg.enabled:
            value = outgoing_session(cfg.role, _current_context(), cfg.session_value)
            if value:
                kwargs["headers"] = _attach_headers(kwargs.get("headers"), cfg, value)
        return _original_request(self, method, url, **kwargs)

    _requests.Session.request = wrapped
    _installed_requests = True


def reset_requests_instrumentation():
    """Test helper."""
    global _installed_requests
    if _installed_requests and _original_request is not None:
        _requests.Session.request = _original_request
        _installed_requests = False


def init_app(app):
    """Extract the original override on every request; instrument outgoing HTTP."""

    @app.before_request
    def _extract_session():
        cfg = BaggageConfig.from_env()
        if not cfg.enabled:
            g.dev_session = None
            return
        g.dev_session = incoming_session(
            cfg.role,
            request.headers.get(cfg.header_name),
            request.cookies.get(cfg.header_name),
            request.args.get(cfg.header_name),
            cfg.session_value,
            enabled=True,
        )

    install_requests()


def install(app=None):
    """One-call setup. Prefer this over hand-written header code."""
    install_requests()
    if app is not None:
        init_app(app)
    return app


class BaggageSession(_requests.Session):
    """Back-compat Session. ``install()`` already covers plain requests."""

    def __init__(self):
        super().__init__()
        install_requests()
