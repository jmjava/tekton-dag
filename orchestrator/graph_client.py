"""
Neo4j graph client for the test-trace regression graph (M9).

Manages the test-to-service mapping graph:
  - Service nodes (app services from the stack)
  - Test nodes (e2e and individual tests)
  - CALLS edges (service A calls service B)
  - TOUCHES edges (test T touches service S)

Query: given a changed app and blast radius, return the minimal test set.
"""

import json
import logging
import os

from neo4j import GraphDatabase

logger = logging.getLogger("orchestrator.graph")

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        uri = os.environ.get("NEO4J_URI", "neo4j://graph-db:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "changeme")
        _driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("Connected to Neo4j at %s", uri)
    return _driver


def close():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def clear_graph():
    """Delete all nodes and relationships."""
    driver = _get_driver()
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    logger.info("Graph cleared")


def create_constraints():
    """Create uniqueness constraints for idempotent ingestion."""
    driver = _get_driver()
    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Service) REQUIRE s.name IS UNIQUE"
        )
        session.run(
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Test) REQUIRE t.id IS UNIQUE"
        )
    logger.info("Constraints created")


def ingest_traces(traces):
    """
    Ingest trace data into Neo4j.

    Each trace has:
      - test_id: stable test identifier
      - test_type: "e2e" or "individual"
      - spans: list of {service, resource}

    Creates:
      - Service nodes for each unique service
      - Test nodes for each unique test
      - TOUCHES relationships (Test)-[:TOUCHES]->(Service)
      - CALLS relationships (Service)-[:CALLS]->(Service) for consecutive spans
    """
    driver = _get_driver()
    with driver.session() as session:
        for trace in traces:
            test_id = trace["test_id"]
            test_type = trace.get("test_type", "unknown")
            spans = trace.get("spans", [])

            session.run(
                "MERGE (t:Test {id: $id}) SET t.type = $type",
                id=test_id,
                type=test_type,
            )

            prev_service = None
            for span in spans:
                svc = span["service"]
                resource = span.get("resource", "")

                session.run("MERGE (s:Service {name: $name})", name=svc)

                session.run(
                    """
                    MATCH (t:Test {id: $tid}), (s:Service {name: $svc})
                    MERGE (t)-[:TOUCHES]->(s)
                    """,
                    tid=test_id,
                    svc=svc,
                )

                if prev_service and prev_service != svc:
                    session.run(
                        """
                        MATCH (a:Service {name: $from}), (b:Service {name: $to})
                        MERGE (a)-[:CALLS]->(b)
                        """,
                        **{"from": prev_service, "to": svc},
                    )

                prev_service = svc

    logger.info("Ingested %d traces", len(traces))


def ingest_from_file(filepath):
    """Load traces from a JSON fixture file and ingest into Neo4j."""
    with open(filepath) as f:
        data = json.load(f)
    traces = data.get("traces", [])
    clear_graph()
    create_constraints()
    ingest_traces(traces)
    return len(traces)


def query_test_plan(changed_app, radius=1):
    """
    Query the minimal test set for a changed app.

    Args:
        changed_app: service name (e.g. "demo-fe")
        radius: blast radius (1 = direct, 2+ = N-hop neighbors)

    Returns:
        dict with:
          - tests: list of {id, type} for tests to run
          - unmapped_area: service name if no tests found, else ""
          - message: human-readable message
    """
    driver = _get_driver()
    with driver.session() as session:
        svc_check = session.run(
            "MATCH (s:Service {name: $name}) RETURN s", name=changed_app
        )
        if not svc_check.single():
            return {
                "tests": [],
                "unmapped_area": changed_app,
                "message": f"No mapped regression; area '{changed_app}' needs tests",
            }

        if radius <= 1:
            result = session.run(
                """
                MATCH (t:Test)-[:TOUCHES]->(s:Service {name: $app})
                RETURN t.id AS id, t.type AS type
                ORDER BY
                  CASE t.type WHEN 'e2e' THEN 0 ELSE 1 END,
                  t.id
                """,
                app=changed_app,
            )
        else:
            result = session.run(
                """
                MATCH (s:Service {name: $app})
                CALL apoc.path.subgraphNodes(s, {
                  relationshipFilter: 'CALLS',
                  minLevel: 0,
                  maxLevel: $radius
                }) YIELD node AS neighbor
                WITH collect(neighbor) AS neighbors
                UNWIND neighbors AS n
                MATCH (t:Test)-[:TOUCHES]->(n)
                RETURN DISTINCT t.id AS id, t.type AS type
                ORDER BY
                  CASE t.type WHEN 'e2e' THEN 0 ELSE 1 END,
                  t.id
                """,
                app=changed_app,
                radius=radius,
            )

        tests = [{"id": r["id"], "type": r["type"]} for r in result]

        if not tests:
            return {
                "tests": [],
                "unmapped_area": changed_app,
                "message": f"No mapped regression; area '{changed_app}' needs tests",
            }

        services_result = session.run(
            """
            MATCH (t:Test)-[:TOUCHES]->(s:Service)
            WHERE t.id IN $ids
            RETURN DISTINCT s.name AS name
            ORDER BY s.name
            """,
            ids=[t["id"] for t in tests],
        )
        services = [r["name"] for r in services_result]

        e2e_count = sum(1 for t in tests if t["type"] == "e2e")
        ind_count = len(tests) - e2e_count
        return {
            "tests": tests,
            "services": services,
            "unmapped_area": "",
            "message": f"{len(tests)} tests selected ({e2e_count} e2e, {ind_count} individual)",
        }


def graph_stats():
    """Return basic graph statistics."""
    driver = _get_driver()
    with driver.session() as session:
        services = session.run("MATCH (s:Service) RETURN count(s) AS c").single()["c"]
        tests = session.run("MATCH (t:Test) RETURN count(t) AS c").single()["c"]
        touches = session.run("MATCH ()-[r:TOUCHES]->() RETURN count(r) AS c").single()["c"]
        calls = session.run("MATCH ()-[r:CALLS]->() RETURN count(r) AS c").single()["c"]
    return {
        "services": services,
        "tests": tests,
        "touches_edges": touches,
        "calls_edges": calls,
    }
