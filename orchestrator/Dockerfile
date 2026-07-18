FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# tekton-dag-common MUST be staged by publish-orchestrator-image.sh
COPY tekton_dag_common_pkg/ /tmp/tekton-dag-common/
RUN test -f /tmp/tekton-dag-common/pyproject.toml \
    || (echo "ERROR: tekton_dag_common_pkg missing pyproject.toml — run scripts/publish-orchestrator-image.sh" >&2; exit 1) \
    && pip install --no-cache-dir /tmp/tekton-dag-common \
    && rm -rf /tmp/tekton-dag-common

COPY . .
RUN rm -rf tekton_dag_common_pkg

EXPOSE 8080

CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "2", "--timeout", "120", "app:create_app()"]
