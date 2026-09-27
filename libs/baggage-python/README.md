# tekton-dag-baggage

Transfers the **original override header** (`x-dev-session` / W3C baggage) hop-to-hop so intercepts can find a PR container somewhere in the stack.

Do not write your own header code. Call `install(app)`. Spec: [docs/BAGGAGE-CONTRACT.md](../../docs/BAGGAGE-CONTRACT.md).

## Installation

```bash
pip install -e /path/to/tekton-dag/libs/baggage-python
```

## Configuration (environment)

| Variable | Default | Description |
|----------|---------|-------------|
| `BAGGAGE_ENABLED` | (unset) | Must be `true` to activate |
| `BAGGAGE_ROLE` | `forwarder` | `originator`, `forwarder`, or `terminal` |
| `BAGGAGE_HEADER_NAME` | `x-dev-session` | Override header |
| `BAGGAGE_KEY` | `dev-session` | W3C baggage key |
| `BAGGAGE_SESSION_VALUE` | (empty) | Originator mint **only** when nothing incoming |

Emit from the stack:

```bash
./scripts/emit-baggage-env.sh --stack stacks/stack-one.yaml --app demo-api
```

## Usage

```python
from flask import Flask
import tekton_dag_baggage

app = Flask(__name__)
tekton_dag_baggage.install(app)  # incoming + instruments requests.Session
```

Originators **adopt** an incoming `pr-42` and copy it downstream. They do not replace it with `BAGGAGE_SESSION_VALUE`.

## Production safety

Inert unless `BAGGAGE_ENABLED=true`. Prefer a dev extra so production installs omit the package.

```bash
pip install -e ".[test]"
pytest
```
