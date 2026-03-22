# GitHub Pages (demo site)

**Live URL:** `https://jmjava.github.io/tekton-dag/`

## How it is published

- Workflow: [.github/workflows/pages.yml](../.github/workflows/pages.yml)
- **Artifact root** is the [`docs/`](../docs/) folder (so `docs/index.html` becomes the site homepage).
- Demo page [`index.html`](index.html) embeds **all 14 segments** plus **full-demo** / **full-demo-with-m12-2**; deep-link with fragments e.g. `…/tekton-dag/#seg-07` (see root [README](../README.md) demo table).
- Checkout uses **`lfs: true`** so large media tracked with Git LFS (e.g. demo MP4s under [`docs/demos/recordings/`](demos/recordings/)) are present in the deployed site. If videos are missing on Pages, confirm those files are committed and that LFS objects are pushed (`git lfs push --all origin main`).
- **Cache-busting:** Before upload, the workflow appends `?v=<short-sha>` to every `demos/recordings/*.mp4` URL in [`index.html`](index.html). That avoids browsers and the Pages CDN serving an **old MP4** while the HTML is already updated (same filename, new bytes). The committed `index.html` in git stays without query strings; only the deployed artifact is rewritten.
- Repository **Settings → Pages**: source should be **GitHub Actions** (not “Deploy from a branch”).

## If the site returns 404

1. **Deployments** — In the repo, open **Actions** and confirm the latest **Deploy to GitHub Pages** run succeeded.
2. **Wrong artifact** — The homepage must be `index.html` at the **root of the uploaded artifact**. Uploading the whole repository (artifact path `.`) leaves no `index.html` at the site root and produces **404** for `/tekton-dag/`.
3. **Environment** — The deploy job uses the `github-pages` environment; ensure any required approval rules are satisfied.

After a green deploy, wait a minute for the CDN to update, then hard-refresh the site.

## Videos on Pages differ from local files

1. **Stale cache (most common)** — After the cache-bust step above, each new deploy uses new `?v=…` URLs. If you still see old content, confirm **Actions → Deploy to GitHub Pages** ran for the commit that updated the MP4s (workflow triggers on `docs/**` pushes to `main`).
2. **LFS** — Run `git lfs pull` locally so your working tree MP4s match the pointers on `main`.
3. **Quick check** — Open the MP4 directly:  
   `https://jmjava.github.io/tekton-dag/demos/recordings/12-regression-suite.mp4`  
   Compare file size or first frame to your local `docs/demos/recordings/12-regression-suite.mp4`.
