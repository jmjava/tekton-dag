from flask import Flask, g, jsonify
import os
import baggage

app = Flask(__name__)
baggage.install(app)

APP_NAME = os.environ.get("APP_NAME", "tekton-dag-flask")


def _hop_report():
    hops = []
    downstream = os.environ.get("DOWNSTREAM_URL", "").strip()
    if downstream:
        try:
            import requests

            url = downstream.rstrip("/") + "/propagation"
            hops.append(requests.get(url, timeout=10).json())
        except Exception as exc:  # pragma: no cover - network optional
            hops.append({"error": str(exc)})
    return {
        "app": APP_NAME,
        "session": getattr(g, "dev_session", None),
        "hops": hops,
    }


@app.route("/")
@app.route("/propagation")
def hello():
    return jsonify(_hop_report())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
