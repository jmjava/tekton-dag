Let's visualize exactly how intercept routing works under the hood.

On screen you see two request paths — blue for normal traffic and green for PR traffic. Both enter the same URL, the same ingress, the same front-end service.

The blue request has no special headers. It flows straight through the standard deployments — the original front-end, the original BFF, the original API. This is production traffic, completely unaffected.

Now watch the green request. It carries the header x-dev-session with value pr-42. When it reaches the intercept point, the routing layer inspects the header. tekton-dag supports two intercept backends — Telepresence and mirrord — and the choice is a single parameter in the pipeline configuration. Regardless of backend, the behavior is the same: the header match redirects the request to the PR-specific pod.

The key insight is that both requests coexist. They share the same cluster, the same ingress, even the same service DNS names. The only difference is the header. This means your PR build is tested in the exact same network topology as production. DNS resolution, service discovery, network policies — everything is identical.

The validate-propagation task in the pipeline verifies this automatically. It sends a request with the header and confirms it arrives at the PR pod at every hop in the propagation chain. The validate-original-traffic task sends a request without the header and confirms it still reaches the original deployment. Both checks must pass before tests run.

The intercept mechanism supports multiple concurrent PRs. PR-42 gets its own deployment, PR-43 gets another. Each is isolated by header value. When the PR merges or closes, the cleanup task in the pipeline's finally block removes the parallel deployment and the intercept rules, leaving the cluster clean.

Same URL, same infrastructure, different backend. That is header-based traffic interception.
