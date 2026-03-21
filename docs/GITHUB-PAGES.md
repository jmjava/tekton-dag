# GitHub Pages (demo site)

**Live URL:** `https://jmjava.github.io/tekton-dag/`

## How it is published

- Workflow: [.github/workflows/pages.yml](../.github/workflows/pages.yml)
- **Artifact root** is the [`docs/`](../docs/) folder (so `docs/index.html` becomes the site homepage).
- Repository **Settings → Pages**: source should be **GitHub Actions** (not “Deploy from a branch”).

## If the site returns 404

1. **Deployments** — In the repo, open **Actions** and confirm the latest **Deploy to GitHub Pages** run succeeded.
2. **Wrong artifact** — The homepage must be `index.html` at the **root of the uploaded artifact**. Uploading the whole repository (artifact path `.`) leaves no `index.html` at the site root and produces **404** for `/tekton-dag/`.
3. **Environment** — The deploy job uses the `github-pages` environment; ensure any required approval rules are satisfied.

After a green deploy, wait a minute for the CDN to update, then hard-refresh the site.
