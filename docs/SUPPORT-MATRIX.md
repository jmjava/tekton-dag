# Support matrix

Canonical machine-readable source: [`support-matrix.yaml`](support-matrix.yaml).
`scripts/check-support-matrix.sh` fails when GitHub Actions jobs drift from it.

Only versions listed here are claimed as tested. Compile-image variants in
`helm/tekton-dag/values.yaml` may include additional tool tags; those are not
supported until a job in this matrix runs them.

## Languages

| Runtime | Tested versions | Primary (every PR) | Compatibility job |
|---------|-----------------|--------------------|-------------------|
| Python | 3.11, 3.12 | 3.12 | baggage-python + tekton-dag-common pytest |
| Node.js | 20, 22 | 22 | baggage-node vitest |
| Java | 21 | 21 | Maven baggage modules |
| PHP | 8.3 | 8.3 | baggage-php PHPUnit |
| Go | 1.26.8 (module 1.26.0) | 1.26.8 | operator CI / local regression |

Python 3.11 is also the docgen/demo-validation interpreter. PHP and Java stay
on a single version because `libs/baggage-php` requires `>=8.3` and the Java
baggage modules compile as source/target 21.

## Kubernetes and Tekton

| Component | Tested version | Cadence |
|-----------|----------------|---------|
| Kind | v0.27.0 | Nightly `cluster-regression`, weekly intercept + Results |
| Tekton Pipelines | v1.6.0 | `scripts/install-tekton.sh` |
| Tekton Triggers | v0.34.0 | `scripts/install-tekton.sh` |
| Tekton Results | v0.20.0 | weekly `results-regression` |

## Cadence

- **Every PR:** [local-regression.yml](../.github/workflows/local-regression.yml) uses the primary versions.
- **Weekly / dispatch / matrix-path PRs:** [compatibility.yml](../.github/workflows/compatibility.yml) runs every language version above.
- **Contract:** `static-quality` and local regression run `check-support-matrix.sh`.
