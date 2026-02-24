# PostgreSQL for Tekton Results

PostgreSQL runs in the `tekton-pipelines` namespace so [Tekton Results](https://github.com/tektoncd/results) can persist pipeline and task run history.

## Install (Kind cluster)

From repo root:

```bash
# After Kind cluster and Tekton Pipelines are installed:
./scripts/install-postgres-kind.sh
```

If your cluster needs a specific StorageClass for the PVC (e.g. `standard`):

```bash
./scripts/install-postgres-kind.sh --storage-class standard
```

**Kind note:** If the PVC stays `Pending`, install a default StorageClass (e.g. [Rancher local-path-provisioner](https://github.com/rancher/local-path-provisioner)) or pass the appropriate `--storage-class`.

## What gets created

- **Secret** `tekton-results-postgres`: `POSTGRES_USER`, `POSTGRES_PASSWORD` (used by Tekton Results and by the Postgres pod).
- **PVC** `tekton-results-postgres-pvc`: 2Gi for Postgres data.
- **Deployment** `tekton-results-postgres`: single Postgres 16 pod.
- **Service** `tekton-results-postgres-service`: DNS name Tekton Results expects by default (`tekton-results-postgres-service.tekton-pipelines.svc.cluster.local`), database `tekton-results`.

## Next step: Tekton Results

After Postgres is running, install Tekton Results (API + Watcher) so pipeline/task runs are stored in the DB:

```bash
./scripts/install-tekton-results.sh
```

Then run a pipeline and verify results are stored:

```bash
./scripts/verify-dag-phase2.sh
./scripts/verify-results-in-db.sh
```

See [Tekton Results install](https://github.com/tektoncd/results/blob/main/docs/install.md) for manual steps.
