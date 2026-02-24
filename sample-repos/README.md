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
