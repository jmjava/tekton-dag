Output terminal/rendered/12-regression-suite.mp4
Output terminal/rendered/12-regression-suite.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Type "# Full regression suite (M12.2) — layered verification"
Enter
Sleep 500ms

Type "# 1. Fast local path — no cluster required"
Enter
Type "# $ ./scripts/run-regression-stream.sh --local-only"
Enter
Sleep 1s
Type "==> Phase 1: verify-dag-phase1.sh ... OK"
Enter
Type "==> pytest orchestrator ... 62 passed"
Enter
Type "==> vitest ... OK"
Enter
Sleep 400ms

Type ""
Enter
Type "# 2. Agent-oriented full run — cluster + Tekton DAG verify"
Enter
Type "# $ ./scripts/run-regression-agent.sh"
Enter
Sleep 1s
Type "==> Freeing ports 9091, 8080 ..."
Enter
Type "==> Phase 1 DAG verify ... PASSED"
Enter
Type "==> Playwright management-gui ... PASSED"
Enter
Type "==> stack-dag-verify PipelineRun ... Succeeded"
Enter
Type "==> Newman orchestrator collection ... PASSED"
Enter
Sleep 500ms

Type ""
Enter
Type "regression exit code: 0"
Enter
Sleep 500ms

Type "# Scripted bar clear — docs and merges can proceed"
Enter
Sleep 3s
