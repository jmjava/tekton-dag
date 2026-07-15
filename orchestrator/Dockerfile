FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# tekton-dag-common is staged into build context by publish-orchestrator-image.sh
COPY tekton_dag_common_pkg/ /tmp/tekton-dag-common/
RUN if [ -f /tmp/tekton-dag-common/pyproject.toml ]; then \
      pip install --no-cache-dir /tmp/tekton-dag-common; \
    fi \
    && rm -rf /tmp/tekton-dag-common

COPY . .
RUN rm -rf tekton_dag_common_pkg

EXPOSE 8080

CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "2", "--timeout", "120", "app:create_app()"]
