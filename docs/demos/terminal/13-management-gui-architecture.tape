Output terminal/rendered/13-management-gui-architecture.mp4
Output terminal/rendered/13-management-gui-architecture.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Type "# Management GUI architecture (M12.2)"
Enter
Sleep 500ms

Type "# Browser -> Vue SPA -> /api/* -> Flask -> Kubernetes API"
Enter
Type "# Cluster credentials never leave the backend"
Enter
Sleep 800ms

Type "# layout: management-gui/"
Enter
Sleep 300ms
Type "management-gui/"
Enter
Type "├── backend/     # Flask + k8s client"
Enter
Type "├── frontend/    # Vue 3 + Pinia + Vue Flow"
Enter
Type "└── README.md"
Enter
Sleep 600ms

Type ""
Enter
Type "# Example: team-scoped PipelineRuns JSON"
Enter
Sleep 400ms
Type '{"items":[{"name":"stack-one-pr-42","status":"Succeeded"}]}'
Enter
Sleep 500ms

Type ""
Enter
Type "# Views: Trigger, Monitor, DAG — each maps to operator workflows"
Enter
Sleep 3s
