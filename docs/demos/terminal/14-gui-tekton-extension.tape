Output terminal/rendered/14-gui-tekton-extension.mp4
Output terminal/rendered/14-gui-tekton-extension.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Type "# Extending the GUI for more Tekton (M12.2)"
Enter
Sleep 500ms

Type "# Pattern: Flask blueprint + k8s_client -> Pinia store -> Vue view"
Enter
Sleep 700ms

Type "# --- management-gui/backend/routes/pipelines.py (excerpt) ---"
Enter
Sleep 300ms
Type "from flask import Blueprint, jsonify, request"
Enter
Type "import k8s_client"
Enter
Type "bp = Blueprint('pipelines', __name__)"
Enter
Type ""
Enter
Type "def _resolve_team(team_name):"
Enter
Type "    # Look up team and return (context, namespace)"
Enter
Sleep 500ms

Type ""
Enter
Type "# --- management-gui/frontend/src/stores/runs.js (excerpt) ---"
Enter
Sleep 300ms
Type "import { get, teamUrl } from '@/api/client'"
Enter
Type "..."
Enter
Type "const data = await get(teamUrl('/pipelineruns?limit=50'))"
Enter
Sleep 500ms

Type ""
Enter
Type "# Checklist: pytest for routes, Playwright for UI, mock k8s in CI"
Enter
Sleep 3s
