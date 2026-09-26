# baggage-spring-boot-starter

Transfers the **original override header** hop-to-hop. Add the starter; do not write interceptors. Spec: [docs/BAGGAGE-CONTRACT.md](../../docs/BAGGAGE-CONTRACT.md).

```xml
<dependency>
  <groupId>com.tektondag</groupId>
  <artifactId>baggage-spring-boot-starter</artifactId>
  <version>1.0.0</version>
</dependency>
```

```properties
baggage.enabled=true
baggage.role=FORWARDER
baggage.header-name=x-dev-session
baggage.baggage-key=dev-session
```

`./scripts/emit-baggage-env.sh --stack stacks/stack-one.yaml --app release-lifecycle-demo --format spring`

Incoming filter reads header, then cookie, then query. A present `pr-42` wins over `baggage.session-value`. Outgoing `RestTemplate` calls get that same value. Other clients: `BaggagePropagator.apply(httpHeaders, properties)`.

`mvn clean test`
