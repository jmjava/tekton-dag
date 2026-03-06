# tekton-dag-baggage

Role-aware W3C baggage / `x-dev-session` middleware for Flask applications.

## Installation

```bash
pip install -e /path/to/tekton-dag/libs/baggage-python
# or from git:
pip install "tekton-dag-baggage @ git+https://github.com/jmjava/tekton-dag.git#subdirectory=libs/baggage-python"
```

## Configuration (environment variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `BAGGAGE_ENABLED` | (unset) | Must be `true` to activate middleware |
| `BAGGAGE_ROLE` | `forwarder` | `originator`, `forwarder`, or `terminal` |
| `BAGGAGE_HEADER_NAME` | `x-dev-session` | Custom header name |
| `BAGGAGE_KEY` | `dev-session` | W3C baggage key |
| `BAGGAGE_SESSION_VALUE` | (empty) | Session value for originator role |

## Usage

```python
from flask import Flask
import tekton_dag_baggage

app = Flask(__name__)
tekton_dag_baggage.init_app(app)
```

For outgoing requests:
```python
session = tekton_dag_baggage.BaggageSession()
session.get("http://downstream-service/api")
```

## Production safety

- **Build-time**: add as an extras group (`pip install myapp[baggage]`). Production installs without the extra.
- **Runtime**: middleware is inert unless `BAGGAGE_ENABLED=true`.

## Testing

```bash
pip install -e ".[test]"
pytest
```
