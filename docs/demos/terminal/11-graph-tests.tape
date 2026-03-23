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
Type `echo '# $ curl -s -X POST localhost:8080/api/graph/ingest ... @tests/fixtures/trace-data.json | jq .'`
Enter
Sleep 500ms
Type `echo '{"ingested": {"services": 3, "tests": 9, "edges": 11}}'`
Enter
Sleep 500ms

Type ""
Enter
Type "# 2. Check graph stats"
Enter
Type `echo '# $ curl -s localhost:8080/api/graph/stats | jq .'`
Enter
Sleep 500ms
Type `echo '{"services": 3, "tests": 9, "touches_edges": 9, "calls_edges": 2}'`
Enter
Sleep 500ms

Type ""
Enter
Type "# 3. Query test plan for demo-api at radius 1"
Enter
Type `echo '# $ curl -s "localhost:8080/api/test-plan?app=demo-api&radius=1" | jq .'`
Enter
Sleep 500ms
Type `echo '{'`
Enter
Type `echo '  "app": "demo-api",'`
Enter
Type `echo '  "radius": 1,'`
Enter
Type `echo '  "tests": ["api-postman", "api-integration", "api-load-test"],'`
Enter
Type `echo '  "count": 3'`
Enter
Type `echo '}'`
Enter
Sleep 500ms

Type ""
Enter
Type "# 4. Expand to radius 2 — includes BFF tests"
Enter
Type `echo '# $ curl -s "localhost:8080/api/test-plan?app=demo-api&radius=2" | jq .'`
Enter
Sleep 500ms
Type `echo '{'`
Enter
Type `echo '  "app": "demo-api",'`
Enter
Type `echo '  "radius": 2,'`
Enter
Type `echo '  "tests": ["api-postman", "api-integration", "api-load-test", "bff-postman", "bff-integration"],'`
Enter
Type `echo '  "count": 5'`
Enter
Type `echo '}'`
Enter
Sleep 500ms

Type ""
Enter
Type "# 5. CLI graph visualization"
Enter
Type `echo '# $ ./scripts/stack-graph.sh stack-one'`
Enter
Sleep 500ms
Type `echo 'demo-fe (originator)'`
Enter
Type `echo '  └──→ release-lifecycle-demo (forwarder)'`
Enter
Type `echo '        └──→ demo-api (terminal)'`
Enter
Sleep 500ms

Type ""
Enter
Type "# Blast-radius query → focused test plan → faster CI ✓"
Enter
Sleep 3s
