Intercept routing depends on one thing: every service in the call chain must propagate the dev-session header. If any service drops it, the routing breaks. The baggage middleware libraries make this automatic across five frameworks.

Every service has a propagation role defined in the stack YAML. An originator starts the chain — it sets the dev-session header on all outgoing requests. A forwarder reads the incoming header, stores it in request context, and attaches it to every downstream call. A terminal accepts the header for routing and logging but does not forward it further.

Let's walk through each framework.

In Spring Boot, the baggage starter auto-configures everything. A servlet filter called BaggageContextFilter reads the incoming header and stores it using OpenTelemetry Baggage and a thread-local context holder. A RestTemplate interceptor called BaggageRestTemplateInterceptor automatically adds the header to every outbound HTTP call. The entire setup activates with a single property: baggage dot enabled equals true. If the property is false or absent, the filter and interceptor are not registered. Zero overhead in production.

For Node and Vue, the library provides createBaggageFetch — a wrapper around the native fetch API that injects the header — and createAxiosInterceptor for Axios-based projects. The default configuration reads from environment variables like VITE underscore BAGGAGE underscore ENABLED, so the browser build can include or exclude baggage at compile time.

In Flask and Python, the init underscore app function registers a before-request hook that extracts the header and stores it on Flask's g object. For outbound calls, BaggageSession extends the standard requests dot Session class to add the header automatically. Same pattern: enabled by an environment variable, zero-cost when disabled.

The PHP implementation uses PSR-15 middleware for inbound requests and a Guzzle middleware for outbound HTTP. The BaggageMiddleware class reads its configuration from environment variables and can be instantiated with a static fromEnv factory method.

All five implementations follow the W3C Baggage specification alongside the custom x-dev-session header. The W3C baggage header carries key-value pairs in a standardized format, which means third-party observability tools can read the routing context without custom parsing.

The critical safety feature is the enabled flag. In every framework, baggage propagation is off by default. It activates only when the environment variable is explicitly set to true. This means you can deploy the middleware to production and it does nothing until you opt in — no accidental header leakage, no performance impact.

Five frameworks. One header contract. Zero application code changes beyond configuration. That is the baggage middleware.
