tekton-dag is designed for multi-team operation from the ground up. Let's see how the Helm chart handles scaling.

We start with a single team — team-alpha — running the three-tier demo stack. The Helm chart deploys the orchestrator, applies all Tekton Tasks and Pipeline definitions, creates ConfigMaps for the stack and team configuration, and optionally provisions a build-cache PVC for faster rebuilds.

Now imagine three teams need their own CI/CD environments. Each team gets its own Helm release with a different teamName value. The chart creates team-scoped ConfigMaps, and each orchestrator instance only manages its own team's stacks and pipelines.

The values.yaml exposes the key knobs. imageRegistry sets where container images are pushed and pulled. interceptBackend chooses between Telepresence and mirrord. compileImages provides the default build image for each tool. And compileImageVariants maps specific language versions — so team-beta can use Java 17 while team-alpha stays on Java 21, all from the same pipeline definitions.

Teams can also inject custom pipeline steps. The pre-build-task and post-build-task parameters let a team wire in their own Tekton Tasks — an image security scan after build, or a data seeding step before tests — without forking the core pipelines. The example tasks in the repo show an image scan hook and a Slack notification hook.

The management GUI provides a team switcher in the web interface. Each team sees their own stacks, pipeline runs, DAG visualizations, and test results — fully isolated.

Watch as a webhook fires for team-beta's PR. Only team-beta's orchestrator picks it up. Only team-beta's pipeline runs. Team-alpha and team-gamma are completely undisturbed.

One chart, multiple releases, full team isolation. That is how tekton-dag scales.
