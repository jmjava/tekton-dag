# M4 §1: Baggage middleware libraries (overview)

Each supported framework has **embedded** baggage middleware (W3C `x-dev-session` / baggage propagation) with all three roles (originator, forwarder, terminal) and production guards. Standalone, publishable libraries are planned in **Milestone 4.1**.

## Current state (embedded in app repos)

| Framework | App repo | Middleware location | Tests |
|-----------|----------|---------------------|--------|
| Spring Boot | tekton-dag-spring-boot | `com.example.dag.baggage.*` | JUnit 5 |
| Spring Legacy | tekton-dag-spring-legacy | `com.example.dag.baggage.*` | JUnit 5 |
| Flask | tekton-dag-flask | `baggage.py` | pytest |
| PHP | tekton-dag-php | `src/Baggage/*` | PHPUnit |
| Vue/Node | tekton-dag-vue-fe | `src/baggage.js` | Vitest |

Configuration: `baggage.enabled` / `BAGGAGE_ENABLED`, `baggage.role` / `BAGGAGE_ROLE`. Header name and baggage key are configurable (defaults: `x-dev-session`, `dev-session`).

## Per-library README (M4.1)

When middleware is extracted into standalone packages (Milestone 4.1), each library will have its own README covering:

- Installation (dependency/add to project)
- Configuration: role, header name, baggage key, production-safety setup
- Usage examples (originator, forwarder, terminal)
- W3C Baggage compliance and merge behavior

Until then, see the app repos above for implementation and tests.
