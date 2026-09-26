# baggage-servlet-filter

Transfers the **original override header** hop-to-hop for servlet/WAR apps. Spec: [docs/BAGGAGE-CONTRACT.md](../../docs/BAGGAGE-CONTRACT.md).

Register `BaggageServletFilter`, then apply outgoing headers with `BaggageOutgoing.apply` — do not copy headers by hand.

```java
BaggageOutgoing.apply(headers, "x-dev-session", "dev-session", BaggageRole.FORWARDER, null);
```

A present incoming `pr-42` is stored in `BaggageContextHolder` and must be the value sent downstream.

```bash
./scripts/emit-baggage-env.sh --stack stacks/stack-one.yaml --app my-war
mvn clean test
```
