Output docs/demos/terminal/rendered/03-bootstrap.mp4
Output docs/demos/terminal/rendered/03-bootstrap.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Type "# Bootstrap stack-one: build and deploy all 3 services"
Enter
Sleep 500ms

Type "./scripts/generate-run.sh --mode bootstrap --stack stack-one.yaml --apply"
Enter
Sleep 2s
Type "# Generated PipelineRun: stack-one-bootstrap-run-abc12"
Enter
Type "# Applying to namespace tekton-pipelines..."
Enter
Sleep 1s

Type "tkn pipelinerun logs stack-one-bootstrap-run-abc12 -f"
Enter
Sleep 1s

Type "[fetch-source]     Cloning platform repo (main)..."
Enter
Sleep 500ms
Type "[fetch-source]     ✓ Cloned at commit a1b2c3d"
Enter
Sleep 300ms

Type "[resolve-stack]    Parsing stacks/stack-one.yaml..."
Enter
Type "[resolve-stack]    Apps: demo-fe (npm), release-lifecycle-demo (maven), demo-api (maven)"
Enter
Type "[resolve-stack]    Propagation chain: demo-fe → release-lifecycle-demo → demo-api"
Enter
Sleep 500ms

Type "[clone-app-repos]  Cloning jmjava/tekton-dag-vue-fe..."
Enter
Type "[clone-app-repos]  Cloning jmjava/tekton-dag-spring-boot..."
Enter
Type "[clone-app-repos]  Cloning jmjava/tekton-dag-spring-boot-gradle..."
Enter
Sleep 500ms

Type "[compile-npm]      npm install && npm run build → demo-fe"
Enter
Sleep 1s
Type "[compile-npm]      ✓ Built in 12s"
Enter

Type "[compile-maven]    mvn -B clean package → release-lifecycle-demo"
Enter
Sleep 1s
Type "[compile-maven]    ✓ Built in 28s"
Enter

Type "[compile-maven]    mvn -B clean package → demo-api"
Enter
Sleep 1s
Type "[compile-maven]    ✓ Built in 25s"
Enter

Type "[containerize]     Kaniko build → 3 images pushed to localhost:5000"
Enter
Sleep 1s
Type "[deploy-full-stack] Deploying demo-fe, release-lifecycle-demo, demo-api..."
Enter
Sleep 1s
Type "[deploy-full-stack] ✓ All 3 pods Running"
Enter
Sleep 500ms

Type ""
Enter
Type "# Bootstrap complete — stack-one is live ✓"
Enter
Sleep 3s
