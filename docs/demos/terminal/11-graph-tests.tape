Output terminal/rendered/11-graph-tests.mp4
Output terminal/rendered/11-graph-tests.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Type "# Test-trace graph — intelligent test selection via Neo4j"
Enter
Sleep 500ms

Type "# 1. Ingest trace data into the graph"
Enter
Type 'curl -s -X POST localhost:8080/api/graph/ingest -H "Content-Type: application/json" \'
Enter
Type '  -d @tests/fixtures/trace-data.json | jq .'
Enter
Sleep 500ms
Type '{"ingested": {"services": 3, "tests": 9, "edges": 11}}'
Enter
Sleep 500ms

Type ""
Enter
Type "# 2. Check graph stats"
Enter
Type "curl -s localhost:8080/api/graph/stats | jq ."
Enter
Sleep 500ms
Type '{"services": 3, "tests": 9, "touches_edges": 9, "calls_edges": 2}'
Enter
Sleep 500ms

Type ""
Enter
Type "# 3. Query test plan for demo-api at radius 1"
Enter
Type 'curl -s "localhost:8080/api/test-plan?app=demo-api&radius=1" | jq .'
Enter
Sleep 500ms
Type '{'
Enter
Type '  "app": "demo-api",'
Enter
Type '  "radius": 1,'
Enter
Type '  "tests": ["api-postman", "api-integration", "api-load-test"],'
Enter
Type '  "count": 3'
Enter
Type '}'
Enter
Sleep 500ms

Type ""
Enter
Type "# 4. Expand to radius 2 — includes BFF tests"
Enter
Type 'curl -s "localhost:8080/api/test-plan?app=demo-api&radius=2" | jq .'
Enter
Sleep 500ms
Type '{'
Enter
Type '  "app": "demo-api",'
Enter
Type '  "radius": 2,'
Enter
Type '  "tests": ["api-postman", "api-integration", "api-load-test", "bff-postman", "bff-integration"],'
Enter
Type '  "count": 5'
Enter
Type '}'
Enter
Sleep 500ms

Type ""
Enter
Type "# 5. CLI graph visualization"
Enter
Type "./scripts/stack-graph.sh stack-one"
Enter
Sleep 500ms
Type "demo-fe (originator)"
Enter
Type "  └──→ release-lifecycle-demo (forwarder)"
Enter
Type "        └──→ demo-api (terminal)"
Enter
Sleep 500ms

Type ""
Enter
Type "# Blast-radius query → focused test plan → faster CI ✓"
Enter
Sleep 3s
