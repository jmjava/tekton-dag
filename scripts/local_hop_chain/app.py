"""Minimal hop-report Flask app for a local originator→forwarder→terminal run."""

from __future__ import annotations

import os

from flask import Flask, g, jsonify

from tekton_dag_baggage import install

app = Flask(__name__)
install(app)

APP_NAME = os.environ.get("APP_NAME", "hop")


@app.route("/")
@app.route("/propagation")
def propagation():
    hops = []
    downstream = os.environ.get("DOWNSTREAM_URL", "").strip()
    if downstream:
        import requests

        url = downstream.rstrip("/") + "/propagation"
        hops.append(requests.get(url, timeout=5).json())
    return jsonify(
        {
            "app": APP_NAME,
            "session": getattr(g, "dev_session", None),
            "hops": hops,
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port)
