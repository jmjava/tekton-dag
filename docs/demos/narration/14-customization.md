tekton-dag is designed to be extended without forking. Every integration point is config-driven, validated by schema, and exposed through Helm values.

Start with the stack schema. The file stacks slash schema dot json defines the shape of a valid stack YAML: app names, build tools, propagation roles, downstream dependencies, and test specifications. When you add a new app or modify an existing one, the schema catches typos and missing fields before the pipeline ever runs.

Adding an application to an existing stack is a YAML edit. You add an entry to the apps array with the app name, its Git repository, its propagation role — originator, forwarder, terminal, or standalone — the build tool, and optionally its downstream dependencies and test collections. The pipeline automatically picks up the new app on the next run.

Build image variants let teams use different language versions without separate pipelines. The Helm chart exposes compileImageVariants — a map of tool-plus-version to container image. Team alpha can run Java seventeen while team beta uses Java twenty-one. The stack YAML specifies which version each app needs via the build dot java dash version field, and the pipeline selects the matching image at runtime.

Hook tasks are the primary extension mechanism for the pipelines. Four insertion points are available: pre-build, post-build, pre-test, and post-test. Each is a pipeline parameter that names a Tekton Task. If the parameter is empty, the pipeline step is skipped via a when expression — zero overhead. If it names a task, that task runs at the appropriate point with access to the stack definition, build outputs, and workspace.

The examples directory includes two reference hooks. The image scan example runs a vulnerability scanner against the built container image after the build step. The Slack notification example posts a message to a channel when the pipeline completes. Both follow the same parameter contract, so teams can write their own hooks without understanding pipeline internals.

Onboarding a new team is a three-step process. Create a directory under teams with a team dot yaml defining the team name, namespace, and stack list. Add a values dot yaml with Helm overrides — registry, intercept backend, build image versions, resource limits. Then install the Helm chart with that team's values. The chart creates team-scoped ConfigMaps, and the team's orchestrator instance only manages its own stacks.

Infrastructure-level settings — the container registry URL, the intercept backend choice between Telepresence and mirrord, pipeline timeouts, and resource profiles — are all Helm values. Changing the registry for a team is a single values dot yaml edit and a Helm upgrade.

Config-only onboarding. Schema-validated stacks. Pluggable hook tasks. Multi-version build images. That is customization in tekton-dag.
