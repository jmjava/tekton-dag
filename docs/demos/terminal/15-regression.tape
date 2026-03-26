Output terminal/rendered/15-regression.mp4
Output terminal/rendered/15-regression.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 35ms
Set Padding 20

Type "# Full regression suite (M12.2) — layered verification"
Enter
Sleep 600ms

Type "# ── Tier 1: fast local path (no cluster) ──"
Enter
Sleep 400ms
Type "# $ ./scripts/run-regression-stream.sh --local-only"
Enter
Sleep 800ms
Type "# ==> Phase 1: verify-dag-phase1.sh ... OK"
Enter
Sleep 200ms
Type "# ==> pytest orchestrator ................ 62 passed"
Enter
Sleep 200ms
Type "# ==> vitest (management-gui frontend) .... OK"
Enter
Sleep 500ms

Type ""
Enter
Type "# ── Tier 2: agent full run (Kind + Tekton + GUI) ──"
Enter
Sleep 400ms
Type "# $ ./scripts/run-regression-agent.sh"
Enter
Sleep 900ms
Type "# ==> Freeing ports 9091, 8080 ..."
Enter
Sleep 200ms
Type "# ==> Phase 1 DAG verify ............... PASSED"
Enter
Sleep 200ms
Type "# ==> Playwright management-gui ........ PASSED"
Enter
Sleep 200ms
Type "# ==> stack-dag-verify PipelineRun ..... Succeeded"
Enter
Sleep 200ms
Type "# ==> Newman orchestrator collection ... PASSED"
Enter
Sleep 400ms

Type ""
Enter
Type "# regression exit code: 0"
Enter
Sleep 600ms

Type "# Bar green → safe to merge docs and demo assets"
Enter
Sleep 800ms
Type "# See: docs/REGRESSION.md · scripts/run-regression*.sh"
Enter
Sleep 4s
