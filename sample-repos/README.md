# Sample app repos for Tekton DAG

Each subdirectory here is a **seed** for a separate GitHub repo. The Tekton pipeline clones app repos by URL (one repo per app), so these must be published as their own repos under **jmjava** before the pipeline can use them.

## Repos (one per app type)

| Repo name | Build tool | Purpose |
|-----------|------------|--------|
| [tekton-dag-vue-fe](https://github.com/jmjava/tekton-dag-vue-fe) | npm | Vue 3 frontend |
| [tekton-dag-spring-boot](https://github.com/jmjava/tekton-dag-spring-boot) | Maven | Spring Boot app |
| [tekton-dag-spring-boot-gradle](https://github.com/jmjava/tekton-dag-spring-boot-gradle) | Gradle | Spring Boot app |
| [tekton-dag-php](https://github.com/jmjava/tekton-dag-php) | Composer | PHP app |
| [tekton-dag-spring-legacy](https://github.com/jmjava/tekton-dag-spring-legacy) | Maven | Spring WAR |
| [tekton-dag-flask](https://github.com/jmjava/tekton-dag-flask) | pip | Flask app |

## Create and push as GitHub repos

From the **tekton-dag** repo root:

```bash
# Prerequisites: gh CLI, authenticated (gh auth login), push access to jmjava
./scripts/create-and-push-sample-repos.sh
```

This will:

1. For each `sample-repos/tekton-dag-*` directory, create a new repo **github.com/jmjava/tekton-dag-xxx** (if it doesn’t exist).
2. Push the directory contents to that repo’s `main` branch.

So each sample app becomes its own cloneable repo and the Tekton scripts can clone them by URL (e.g. in stack YAML `repo: jmjava/tekton-dag-vue-fe`).

- **Dry run:** `./scripts/create-and-push-sample-repos.sh --dry-run`
- **Single repo:** `./scripts/create-and-push-sample-repos.sh tekton-dag-flask`
