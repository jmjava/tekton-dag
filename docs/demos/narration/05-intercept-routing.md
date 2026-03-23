Let's visualize exactly how intercept routing works under the hood.

On screen you see two request paths — blue for normal traffic and green for PR traffic. Both enter the same URL, the same ingress, the same front-end service.

The blue request has no special headers. It flows straight through the standard deployments — the original front-end, the original BFF, the original API. This is baseline traffic to the steady deployment, completely unaffected.

Now watch the green request. It carries the dev-session header with pull request number forty-two. When it reaches the intercept point, the routing layer inspects the header. tekton-dag supports two intercept backends — Telepresence and mirrord — and the choice is a single parameter in the pipeline configuration. Regardless of backend, the behavior is the same: the header match redirects the request to the pull-request-specific pod.

The key insight is that both requests coexist. They share the same cluster, the same ingress, even the same service DNS names. The only difference is the header. In practice you usually run this in a validation or pre-production cluster that mirrors production's shape, so DNS resolution, service discovery, and network policies match what you will see after promote — while keeping customer-facing production on its own cluster until you release.

The validate propagation task in the pipeline verifies this automatically. It sends a request with the header and confirms it arrives at the pull-request pod at every hop in the propagation chain. The validate original traffic task sends a request without the header and confirms it still reaches the baseline deployment. Both checks must pass before tests run.

The intercept mechanism supports multiple concurrent pull requests. Pull request forty-two gets its own deployment, pull request forty-three gets another. Each is isolated by header value. When the pull request merges or closes, the cleanup task in the pipeline's finally block removes the parallel deployment and the intercept rules, leaving the cluster clean.

Same URL, same infrastructure, different backend. That is header-based traffic interception.
