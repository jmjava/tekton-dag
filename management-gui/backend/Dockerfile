FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# tekton-dag-common is staged into build context by publish-management-gui-image.sh
COPY tekton_dag_common_pkg/ /tmp/tekton-dag-common/
RUN test -f /tmp/tekton-dag-common/pyproject.toml \
    || (echo "ERROR: tekton_dag_common_pkg missing pyproject.toml — run scripts/publish-management-gui-image.sh" >&2; exit 1) \
    && pip install --no-cache-dir /tmp/tekton-dag-common \
    && rm -rf /tmp/tekton-dag-common

COPY . .
RUN rm -rf tekton_dag_common_pkg

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:create_app()"]
