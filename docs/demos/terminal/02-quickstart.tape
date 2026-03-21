Output terminal/rendered/02-quickstart.mp4
Output terminal/rendered/02-quickstart.gif
Set FontSize 14
Set Width 1400
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Type "# tekton-dag Quick Start"
Enter
Sleep 500ms

Type "# 1. Create Kind cluster with local registry"
Enter
Sleep 300ms
Type "./scripts/kind-with-registry.sh"
Enter
Sleep 3s
Type "# ✓ Kind cluster 'tekton-dag' created, registry at localhost:5001"
Enter
Sleep 500ms

Type "# 2. Install Tekton Pipelines"
Enter
Sleep 300ms
Type "./scripts/install-tekton.sh"
Enter
Sleep 3s
Type "# ✓ Tekton Pipelines v0.56 installed, controller ready"
Enter
Sleep 500ms

Type "# 3. Publish build images (npm, maven, gradle, pip, composer, mirrord)"
Enter
Sleep 300ms
Type "./scripts/publish-build-images.sh"
Enter
Sleep 3s
Type "# ✓ 6 build images pushed to localhost:5001"
Enter
Sleep 500ms

Type "# 4. Apply tasks and pipelines"
Enter
Sleep 300ms
Type "kubectl apply -f tasks/ -f pipeline/"
Enter
Sleep 2s
Type "# ✓ 23 tasks + 5 pipelines applied"
Enter
Sleep 500ms

Type ""
Enter
Type "# Ready! Full stack-aware CI/CD on a local Kind cluster ✓"
Enter
Sleep 3s
