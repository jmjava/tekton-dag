"""Allow ``python -m tekton_dag_common.baggage_contract`` via package dispatch."""

from tekton_dag_common.baggage_contract import main

if __name__ == "__main__":
    raise SystemExit(main())
