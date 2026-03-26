Output terminal/rendered/08-orchestrator-api.mp4
Output terminal/rendered/08-orchestrator-api.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Type "# Orchestrator API — the brain of tekton-dag"
Enter
Sleep 500ms

Type "# Health checks"
Enter
Type `echo '# $ curl -s localhost:8080/healthz | jq .'`
Enter
Sleep 500ms
Type `echo '{"status": "ok"}'`
Enter
Sleep 300ms

Type `echo '# $ curl -s localhost:8080/readyz | jq .'`
Enter
Sleep 500ms
Type `echo '{"status": "ready", "stacks_loaded": 2, "teams": ["default"]}'`
Enter
Sleep 500ms

Type "# List stacks"
Enter
Type `echo '# $ curl -s localhost:8080/api/stacks | jq .'`
Enter
Sleep 500ms
Type `echo '['`
Enter
Type `echo '  {"name": "stack-one", "apps": ["demo-fe","release-lifecycle-demo","demo-api"]},'`
Enter
Type `echo '  {"name": "stack-two", "apps": ["vendor-fe","vendor-middleware","vendor-adapter","internal-api","notifications-svc"]}'`
Enter
Type `echo ']'`
Enter
Sleep 500ms

Type "# Trigger a PR pipeline"
Enter
Type `echo '# $ curl -s -X POST localhost:8080/api/run ... (mode=pr stack=stack-one app=demo-api pr=42) | jq .'`
Enter
Sleep 1s
Type `echo '{"pipelinerun": "stack-one-pr-42-run-xyz78", "status": "created"}'`
Enter
Sleep 500ms

Type "# Query test plan from Neo4j graph"
Enter
Type `echo '# $ curl -s "localhost:8080/api/test-plan?app=demo-api&radius=1" | jq .'`
Enter
Sleep 500ms
Type `echo '{"app": "demo-api", "radius": 1, "tests": ["api-post","api-intg","api-load"], "count": 3}'`
Enter
Sleep 500ms

Type "# Graph stats"
Enter
Type `echo '# $ curl -s localhost:8080/api/graph/stats | jq .'`
Enter
Sleep 500ms
Type `echo '{"services": 3, "tests": 9, "touches_edges": 9, "calls_edges": 2}'`
Enter
Sleep 500ms

Type "# Recent pipeline runs"
Enter
Type `echo '# $ curl -s localhost:8080/api/runs | jq .[0]'`
Enter
Sleep 500ms
Type `echo '{"name": "stack-one-pr-42-run-xyz78", "status": "Succeeded", "duration": "2m14s"}'`
Enter
Sleep 500ms

Type ""
Enter
Type "# Full REST API for automation and integration ✓"
Enter
Sleep 3s
