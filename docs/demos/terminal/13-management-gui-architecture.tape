Output terminal/rendered/13-management-gui-architecture.mp4
Output terminal/rendered/13-management-gui-architecture.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 35ms
Set Padding 20

Type "# Management GUI architecture (M12.2)"
Enter
Sleep 500ms

Type "# Trust boundary: browser never holds kubeconfig or tokens"
Enter
Sleep 500ms
Type "# Browser → Vue SPA → /api/* → Flask → Kubernetes API"
Enter
Sleep 700ms

Type ""
Enter
Type "# Repo layout"
Enter
Sleep 300ms
Type "# management-gui/"
Enter
Type "# ├── backend/          # Flask, Gunicorn, k8s python client"
Enter
Type "# ├── frontend/         # Vue 3, Vite, Pinia, Vue Flow"
Enter
Type "# └── tests/            # pytest + Playwright + Postman"
Enter
Sleep 600ms

Type ""
Enter
Type "# Team switcher → backend resolves context + namespace"
Enter
Sleep 500ms
Type `echo '# $ curl -s localhost:5000/api/teams | head -c 80'`
Enter
Sleep 600ms
Type `echo '{"teams":["alpha","beta"],"active":"alpha"}...'`
Enter
Sleep 600ms

Type ""
Enter
Type "# Example: scoped PipelineRuns (truncated JSON)"
Enter
Sleep 400ms
Type `echo '{"items":[{"name":"stack-one-pr-42","status":"Succeeded"}]}'`
Enter
Sleep 500ms

Type ""
Enter
Type "# Operator flows: Trigger run · Monitor TaskRuns · Inspect DAG"
Enter
Sleep 500ms
Type "# Network tab shows only same-origin /api — no direct cluster calls"
Enter
Sleep 5s
