# Sample app repos for Tekton DAG

Sample apps are **separate GitHub repos** under **jmjava**. The Tekton pipeline clones them via SSH when running the bootstrap/PR pipelines.

## Clone into `~/github/jmjava`

From your home or any parent dir:

```bash
mkdir -p ~/github/jmjava
cd ~/github/jmjava

git clone git@github.com:jmjava/tekton-dag-flask.git
git clone git@github.com:jmjava/tekton-dag-php.git
git clone git@github.com:jmjava/tekton-dag-spring-boot.git
git clone git@github.com:jmjava/tekton-dag-spring-boot-gradle.git
git clone git@github.com:jmjava/tekton-dag-spring-legacy.git
git clone git@github.com:jmjava/tekton-dag-vue-fe.git
```

Then edit and push from each repo (e.g. `cd ~/github/jmjava/tekton-dag-spring-boot && git add -A && git commit -m "..." && git push`).

## Repos (one per app type)

| Repo | Clone (SSH) | Build tool |
|------|-------------|------------|
| tekton-dag-vue-fe | `git@github.com:jmjava/tekton-dag-vue-fe.git` | npm |
| tekton-dag-spring-boot | `git@github.com:jmjava/tekton-dag-spring-boot.git` | Maven |
| tekton-dag-spring-boot-gradle | `git@github.com:jmjava/tekton-dag-spring-boot-gradle.git` | Maven / Gradle |
| tekton-dag-php | `git@github.com:jmjava/tekton-dag-php.git` | Composer |
| tekton-dag-spring-legacy | `git@github.com:jmjava/tekton-dag-spring-legacy.git` | Maven |
| tekton-dag-flask | `git@github.com:jmjava/tekton-dag-flask.git` | pip |

Stacks reference them as `repo: jmjava/tekton-dag-<name>` in `stacks/*.yaml`.

## VS Code workspace (run and debug from the IDE)

The platform repo’s launch configs (`.vscode/launch.json`) expect each app repo to be a **workspace folder** in a **multi-root workspace**, with a **folder name** that matches the repo name (e.g. `tekton-dag-vue-fe`). That way `cwd` and sources resolve correctly when you run **Vue (demo-fe): Launch & debug** or **Spring Boot (release-lifecycle-demo): Attach**, etc.

**How to set it up:**

1. Clone this repo (tekton-dag) and the sample app repos (e.g. into `~/github/jmjava` as above).
2. In VS Code/Cursor, open the **tekton-dag** folder (platform repo).
3. **File → Add Folder to Workspace…** and add each app repo folder (e.g. `~/github/jmjava/tekton-dag-vue-fe`). The **name** VS Code uses for each root is the folder’s last path segment — so cloning into `~/github/jmjava/tekton-dag-vue-fe` gives the workspace folder name `tekton-dag-vue-fe`, which matches the launch configs.
4. **File → Save Workspace As…** and save as e.g. `tekton-dag.code-workspace` inside the platform repo. Reopen that workspace file later to get tekton-dag + all app repos in one window with working launch configs.

If you add a repo from a path whose folder name doesn’t match (e.g. `my-apps/tekton-dag-vue-fe`), the folder name in the workspace may be `tekton-dag-vue-fe` anyway; if not, the launch configs that reference `${workspaceFolder:tekton-dag-vue-fe}` won’t find it. Prefer cloning into a parent dir like `~/github/jmjava` so each repo root has the expected name.

For the actual debug flow (start app → create Telepresence intercept → trigger traffic), see [../.vscode/README.md](../.vscode/README.md).
