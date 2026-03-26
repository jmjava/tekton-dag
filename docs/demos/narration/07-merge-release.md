The pull request passed. Tests are green. The developer clicks merge. What happens next?

A GitHub webhook fires and the orchestrator generates a PipelineRun in merge mode. Unlike the pull-request pipeline, which builds only the changed service, the merge pipeline produces a release-quality artifact with proper semantic versioning.

The first interesting step is the version bump task running in release mode. During the pull-request cycle, the version file tracked a release candidate suffix — something like zero dot one dot zero dash rc dot three. The release version bump strips that suffix. The app version becomes zero dot one dot zero — a clean release number.

Next, the pipeline compiles and containerizes the merged code, just like the PR build, but tagged with the merge commit SHA. The compile tasks use the same parameterized build images — Maven, Gradle, npm, pip, or Composer — with the resource profiles configured per team.

Here is where the merge pipeline diverges from the PR pipeline. The tag release images task uses crane — a fast, daemon-less container tool — to copy the built image and re-tag it with the release semver. The image registry now holds the app at v zero dot one dot zero. No rebuild needed — crane copies the layers directly.

After tagging, the pipeline bumps the version file to the next development cycle. Zero dot one dot zero becomes zero dot one dot one dash rc dot zero — ready for the next pull request to start incrementing the release candidate again. This version commit is pushed back to the repository automatically using SSH credentials.

If the team has configured hook tasks, they run at the right points. A post-build hook might trigger an image security scan or generate a software bill of materials. A pre-test hook might seed test data. These are optional Tekton Tasks wired through pipeline parameters — no need to fork the core pipeline definition.

The result is a release-tagged container image sitting in your registry, ready for promotion. How you promote — Argo Rollouts, a Helm upgrade, a manual release script — is up to your deployment strategy. tekton-dag handles everything up to the release artifact.

Pull request tested. Version promoted. Image tagged. Hooks executed. Version file bumped for the next cycle. That is the merge and release pipeline.
