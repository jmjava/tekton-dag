# Management GUI

Web UI for **monitoring Tekton pipelines**, **triggering runs**, **viewing stack DAGs**, **browsing Git repos**, and related operator workflows. Built as a **Vue 3** single-page app (**Vite**) with a **Flask** backend that talks to Kubernetes and the orchestrator according to deployment configuration.

## Architecture

- **`frontend/`** — Vue 3 + Vite; dev server proxies `/api` to the backend.
- **`backend/`** — Flask app (`app.py`), tests under `backend/tests/`.
- **Docker** — `backend/Dockerfile` for containerizing the backend (frontend assets may be built and served per your deploy path).

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Dev server (default **port 3000**); API calls under `/api` are proxied to the Flask backend.

## Backend setup

```bash
cd backend
pip install -r requirements.txt
python3 app.py
```

Listens on **port 5000** by default; override with env **`PORT`**.

## Testing

**Frontend (Playwright E2E):**

```bash
cd frontend
npx playwright test
```

**69** E2E tests across the suite (`npx playwright test --list`).

**Backend (pytest):**

```bash
cd backend
python3 -m pytest tests/ -v
```

**56** tests.

## Features (overview)

- **Team switcher** — operate in the context of a team / namespace configuration.
- **DAG visualization** — graph view of stack relationships.
- **Pipeline monitor** — status and history of runs.
- **Trigger** — start bootstrap / PR-style flows where supported.
- **Test results** — surface test outcome information from the platform.
- **Git browser** — browse repository content via the backend.
- **Tekton Dashboard embed** — quick deep-link / embed to the dashboard where configured.

For deployment with the rest of the platform, use the **`helm/tekton-dag`** chart and its management-GUI values.

**Extending the UI** (new Tekton-backed screens, API pattern): [docs/MANAGEMENT-GUI-EXTENSION.md](../docs/MANAGEMENT-GUI-EXTENSION.md).
