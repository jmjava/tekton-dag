Output terminal/rendered/14-gui-tekton-extension.mp4
Output terminal/rendered/14-gui-tekton-extension.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 35ms
Set Padding 20

Type "# Extending the GUI for more Tekton (M12.2)"
Enter
Sleep 500ms

Type "# Pattern: route → k8s_client → JSON → Pinia → Vue view"
Enter
Sleep 700ms

Type "# --- backend: Flask blueprint (excerpt) ---"
Enter
Sleep 300ms
Type "# from flask import Blueprint, jsonify, request"
Enter
Type "# import k8s_client"
Enter
Type "# bp = Blueprint('pipelines', __name__)"
Enter
Sleep 400ms
Type "# @bp.get('/pipelineruns')"
Enter
Type "# def list_runs(team):"
Enter
Type "#     ns = _resolve_team(team)"
Enter
Type "#     return jsonify(k8s_client.list_pipelineruns(ns))"
Enter
Sleep 600ms

Type ""
Enter
Type "# --- frontend: store calls team-scoped API ---"
Enter
Sleep 300ms
Type `echo '# import { get, teamUrl } from @/api/client'`
Enter
Type `echo '# export const useRunsStore = defineStore(runs, {'`
Enter
Type `echo '#   async fetchRuns() {'`
Enter
Type `echo '#     const data = await get(teamUrl("/pipelineruns?limit=50"))'`
Enter
Type `echo '#     this.items = data.items'`
Enter
Type `echo '#   }'`
Enter
Type `echo '# })'`
Enter
Sleep 600ms

Type ""
Enter
Type "# Quality bar: pytest routes · Playwright E2E · mock k8s in CI"
Enter
Sleep 500ms
Type "# Ship small PRs: schema + API + store + view + one E2E"
Enter
Sleep 6s
