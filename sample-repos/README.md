# Sample app repos for Tekton DAG

Each subdirectory here is a **seed** for a separate GitHub repo. The Tekton pipeline clones app repos via **SSH** (one repo per app), so these must be published as their own repos under **jmjava** before the pipeline can use them.

## Repos (one per app type)

Clone via SSH: `git@github.com:jmjava/<repo-name>.git`

| Repo name | Clone (SSH) | Build tool | Purpose |
|-----------|-------------|------------|--------|
| [tekton-dag-vue-fe](https://github.com/jmjava/tekton-dag-vue-fe) | `git@github.com:jmjava/tekton-dag-vue-fe.git` | npm | Vue 3 frontend |
| [tekton-dag-spring-boot](https://github.com/jmjava/tekton-dag-spring-boot) | `git@github.com:jmjava/tekton-dag-spring-boot.git` | Maven | Spring Boot app |
| [tekton-dag-spring-boot-gradle](https://github.com/jmjava/tekton-dag-spring-boot-gradle) | `git@github.com:jmjava/tekton-dag-spring-boot-gradle.git` | Gradle | Spring Boot app |
| [tekton-dag-php](https://github.com/jmjava/tekton-dag-php) | `git@github.com:jmjava/tekton-dag-php.git` | Composer | PHP app |
| [tekton-dag-spring-legacy](https://github.com/jmjava/tekton-dag-spring-legacy) | `git@github.com:jmjava/tekton-dag-spring-legacy.git` | Maven | Spring WAR |
| [tekton-dag-flask](https://github.com/jmjava/tekton-dag-flask) | `git@github.com:jmjava/tekton-dag-flask.git` | pip | Flask app |

## Create and push as GitHub repos

From the **tekton-dag** repo root:

```bash
# Prerequisites: gh CLI, authenticated (gh auth login), push access to jmjava
./scripts/create-and-push-sample-repos.sh
```

This will:

1. For each `sample-repos/tekton-dag-*` directory, create a new repo **github.com/jmjava/tekton-dag-xxx** (if it doesn’t exist).
2. Push the directory contents to that repo’s `main` branch.

So each sample app becomes its own cloneable repo and the Tekton pipeline clones them via SSH (stack YAML uses `repo: jmjava/tekton-dag-vue-fe`, which becomes `git@github.com:jmjava/tekton-dag-vue-fe.git`).

- **Dry run:** `./scripts/create-and-push-sample-repos.sh --dry-run`
- **Single repo:** `./scripts/create-and-push-sample-repos.sh tekton-dag-flask`
