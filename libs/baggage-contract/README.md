# Baggage contract (v1)

Canonical **incoming / outgoing** rules for every tekton-dag baggage client.

Apps must **not** write their own header logic. Add the library for the runtime, call `install()` (or take the Spring starter), and set env from the stack:

```bash
python -m tekton_dag_common.baggage_contract emit --stack stacks/stack-one.yaml --app demo-fe
./scripts/baggage-doctor.sh --stack stacks/stack-one.yaml
```

| File | Purpose |
|------|---------|
| [`contract.json`](contract.json) | Defaults, env names, role table, infer rules |
| [`vectors.json`](vectors.json) | Shared codec + role-resolution fixtures |
| [`../../docs/BAGGAGE-CONTRACT.md`](../../docs/BAGGAGE-CONTRACT.md) | Human spec |

Reference implementation: [`tekton_dag_common.baggage_contract`](../tekton-dag-common/tekton_dag_common/baggage_contract.py). Each language library implements the same functions and runs the same vectors.
