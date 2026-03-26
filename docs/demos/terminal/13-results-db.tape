Output terminal/rendered/13-results-db.mp4
Output terminal/rendered/13-results-db.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Type "# Tekton Results — persistent pipeline history"
Enter
Sleep 500ms

Type "# Verify Results API is running"
Enter
Type `echo '# $ kubectl get pods -n tekton-pipelines -l app=tekton-results-api'`
Enter
Sleep 500ms
Type `echo 'NAME                                  READY   STATUS    AGE'`
Enter
Type `echo 'tekton-results-api-7d8f9b6c4-k2m3n   1/1     Running   2d'`
Enter
Sleep 300ms

Type ""
Enter
Type "# Query stored pipeline results"
Enter
Type `echo '# $ ./scripts/verify-results-in-db.sh'`
Enter
Sleep 1s

Type `echo '==> Querying Tekton Results API...'`
Enter
Type `echo '==> Found 5 PipelineRun records:'`
Enter
Sleep 300ms
Type `echo '  stack-one-bootstrap-run-abc12    Succeeded   3m42s   2026-03-18T10:15:00Z'`
Enter
Type `echo '  stack-one-pr-41-run-def34        Succeeded   2m08s   2026-03-18T14:22:00Z'`
Enter
Type `echo '  stack-one-pr-42-run-xyz78        Succeeded   2m14s   2026-03-19T09:30:00Z'`
Enter
Type `echo '  stack-two-bootstrap-run-ghi56    Succeeded   5m31s   2026-03-19T11:00:00Z'`
Enter
Type `echo '  stack-one-pr-43-run-jkl90        Failed      1m45s   2026-03-19T15:10:00Z'`
Enter
Sleep 500ms

Type ""
Enter
Type `echo '==> Found 18 TaskRun records across 5 PipelineRuns'`
Enter
Type `echo '==> All results persisted in Postgres ✓'`
Enter
Sleep 500ms

Type ""
Enter
Type "# Persistent audit trail for every pipeline execution ✓"
Enter
Sleep 3s
