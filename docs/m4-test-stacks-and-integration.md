# M4 §1.6–1.7: Test stacks and integration test matrix

**Pre-commit / CI check:** Run `./scripts/verify-m4-stacks-and-labels.sh` to validate stack YAML parse, required fields, pipeline/task version labels, and that `generate-run.sh` accepts a test stack (dry-run).

## Test stacks (framework-in-role coverage)

Test-only stack YAMLs under `stacks/` exercise every supported framework in each propagation role. Use these with the PR pipeline and `validate-stack-propagation` to confirm baggage propagation across framework combinations.

| Stack file | Purpose | Chain |
|------------|---------|--------|
| `test-stack-flask-forwarder.yaml` | Flask as **forwarder** | Vue (originator) → Flask (forwarder) → Spring Boot (terminal) |
| `test-stack-php-forwarder.yaml` | PHP as **forwarder** | Vue (originator) → PHP (forwarder) → Spring Legacy (terminal) |
| `test-stack-flask-originator.yaml` | Flask as **originator** | Flask (originator) → Spring Boot (terminal) |
| `test-stack-spring-boot-originator.yaml` | Spring Boot as **originator** | Spring Boot (originator) → Spring Boot (terminal) |
| `test-stack-multi-hop-mixed.yaml` | Multi-hop mixed frameworks | Spring Boot → Flask → PHP → Spring Legacy (originator → forwarder → forwarder → terminal) |

Existing production stacks already cover:

- **Vue (originator)**: `stack-one.yaml`, `stack-two-vendor.yaml`
- **Spring Boot (forwarder)**: `stack-one.yaml`
- **Spring Boot / Gradle (forwarder)**: `stack-two-vendor.yaml`
- **PHP, Spring Legacy, Flask (terminal)**: `stack-two-vendor.yaml`

## Integration tests: how to run

1. **Bootstrap a test namespace** (e.g. `tekton-test`):
   ```bash
   ./scripts/bootstrap-namespace.sh tekton-test
   ```

2. **Run PR pipeline against a test stack** with one app as the changed (intercepted) app:
   ```bash
   NAMESPACE=tekton-test ./scripts/generate-run.sh --mode pr --stack test-stack-flask-forwarder.yaml --app analytics-api --pr 1 \
     --registry localhost:5000 --storage-class "" --apply
   ```

3. The pipeline runs `validate-stack-propagation` with the stack JSON, propagation chain, and intercept header. The task:
   - Sends a request to the entry (originator) with `x-dev-session` and W3C `baggage`
   - Verifies the chain and that the header reaches each hop up to the deepest intercepted app

4. **Cross-framework matrix** (CI or manual): for each test stack, run the PR pipeline with each app in the chain as `--app` (changed-app) to ensure propagation works for every intercepted position:

   | Stack | changed-app (intercepted) |
   |-------|---------------------------|
   | test-stack-flask-forwarder | demo-fe, analytics-api, demo-api |
   | test-stack-php-forwarder | vendor-fe, vendor-adapter, internal-api |
   | test-stack-flask-originator | analytics-api, demo-api |
   | test-stack-spring-boot-originator | release-lifecycle-demo, demo-api |
   | test-stack-multi-hop-mixed | release-lifecycle-demo, analytics-api, vendor-adapter, internal-api |

## Unit tests vs integration

- **Unit tests**: per app repo (JUnit/Pytest/PHPUnit/Vitest) cover W3C codec, role behavior, and production guard. Run in CI on each app.
- **Integration**: test stacks + pipeline runs above validate that the full chain propagates headers when deployed in-cluster with Telepresence intercepts.
