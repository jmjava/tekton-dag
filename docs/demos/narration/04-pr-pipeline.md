Here is where tekton-dag really shines — the pull request pipeline.

When a developer opens a pull request against an application repo, a GitHub webhook fires. The orchestrator identifies which stack contains that repo using the registry mapping, determines the changed app, and generates a PipelineRun in pull-request mode. Unlike the bootstrap, the pull-request pipeline only builds the changed service — not the entire stack.

Let's watch it execute. The generate-run script accepts the mode, the repo name, and the pull request number. It produces a complete PipelineRun manifest.

The pipeline starts with fetch source — cloning the platform repo to get the stack definitions. Then resolve stack parses the DAG and identifies the build apps and propagation chain. Next, clone app repos checks out each app repo, using the pull-request branch for the changed app.

The pull-request snapshot tag task generates a unique image tag for this pull-request build so it never collides with real releases. Then build select tool apps routes the changed app to the correct compile task — Maven, Gradle, npm, pip, or Composer — running inside the appropriate build image. Kaniko containerizes the result and pushes it to the registry, with optional cache repository support for faster rebuilds.

Now the interesting part. The pipeline deploys a parallel instance of the changed service — the pull-request build runs alongside the existing baseline deployment in the cluster where you validate changes, not in your separate production cluster. It then configures traffic interception using Telepresence or mirrord so that any request carrying the dev-session header, with a value matching this pull request number, gets routed to the new build.

The validate propagation task confirms the header travels correctly through the entire chain. Validate original traffic confirms that requests without the header still reach the baseline pods. Then query test plan calls the orchestrator to ask the Neo4j graph which tests are relevant for the changed app. Run tests executes only those tests, with the dev-session header injected.

In the finally block, the pipeline cleans up pull-request pods and posts a comment to the GitHub pull request with the test summary and a link to the Tekton Dashboard run. If tests passed, a version bump task records the release candidate.

If tests pass, the pull request is safe to merge. If they fail, only the pull-request traffic was affected — baseline traffic and your production cluster stay out of the blast radius.
