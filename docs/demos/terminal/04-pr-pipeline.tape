Output terminal/rendered/04-pr-pipeline.mp4
Output terminal/rendered/04-pr-pipeline.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Type "# PR Pipeline: test a change to demo-api"
Enter
Sleep 500ms

Type "./scripts/generate-run.sh --mode pr --repo tekton-dag-spring-boot-gradle --pr 42 --apply"
Enter
Sleep 1s
Type "# Resolved: repo → stack-one, changed-app → demo-api"
Enter
Type "# Generated PipelineRun: stack-one-pr-42-run-xyz78"
Enter
Sleep 500ms

Type "tkn pipelinerun logs stack-one-pr-42-run-xyz78 -f"
Enter
Sleep 1s

Type "[fetch-source]       ✓ Platform repo cloned"
Enter
Sleep 300ms
Type "[resolve-stack]      ✓ Stack parsed — changed-app: demo-api (maven)"
Enter
Sleep 300ms
Type "[clone-app-repos]    ✓ demo-api checked out at PR branch feature/new-endpoint"
Enter
Sleep 300ms
Type "[pr-snapshot-tag]    ✓ Tag: demo-api:pr-42-snap-20260319"
Enter
Sleep 300ms

Type "[compile-maven]      mvn -B clean package → demo-api"
Enter
Sleep 1s
Type "[compile-maven]      ✓ Built in 24s"
Enter

Type "[containerize]       Kaniko → localhost:5000/demo-api:pr-42-snap-20260319"
Enter
Sleep 500ms
Type "[containerize]       ✓ Pushed"
Enter

Type "[deploy-intercepts]  Deploying PR pod alongside baseline (validation cluster)..."
Enter
Type "[deploy-intercepts]  Intercept backend: telepresence"
Enter
Type "[deploy-intercepts]  Header match: x-dev-session=pr-42"
Enter
Sleep 500ms
Type "[deploy-intercepts]  ✓ PR pod running, intercept active"
Enter

Type "[validate-propagation] Sending request with x-dev-session: pr-42..."
Enter
Type "[validate-propagation] demo-fe → release-lifecycle-demo → demo-api(PR) ✓"
Enter
Sleep 300ms

Type "[validate-original]  Sending request without header..."
Enter
Type "[validate-original]  demo-fe → release-lifecycle-demo → demo-api(prod) ✓"
Enter
Sleep 300ms

Type "[query-test-plan]    Querying Neo4j: blast radius 1 for demo-api"
Enter
Type "[query-test-plan]    Tests: api-post, api-intg, api-load (3 tests)"
Enter
Sleep 300ms

Type "[run-tests]          Running 3 tests with x-dev-session: pr-42..."
Enter
Sleep 1s
Type "[run-tests]          api-post: PASSED (1.2s)"
Enter
Type "[run-tests]          api-intg: PASSED (3.4s)"
Enter
Type "[run-tests]          api-load: PASSED (8.1s)"
Enter
Type "[run-tests]          ✓ 3/3 passed"
Enter
Sleep 300ms

Type "[finally: cleanup]   Removing PR pod and intercept rules..."
Enter
Type "[finally: cleanup]   ✓ Clean"
Enter
Type "[finally: pr-comment] Posted summary to PR #42 ✓"
Enter
Sleep 500ms

Type ""
Enter
Type "# PR pipeline complete — all tests passed, PR is safe to merge ✓"
Enter
Sleep 3s
