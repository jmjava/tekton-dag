# baggage-servlet-filter

Role-aware W3C baggage / `x-dev-session` servlet filter for legacy Spring / WAR-deployed apps.

## Installation

```xml
<dependency>
  <groupId>com.tektondag</groupId>
  <artifactId>baggage-servlet-filter</artifactId>
  <version>1.0.0</version>
</dependency>
```

Install locally first: `cd libs/baggage-servlet-filter && mvn install`

## Configuration (web.xml)

```xml
<filter>
  <filter-name>baggageFilter</filter-name>
  <filter-class>com.tektondag.baggage.BaggageServletFilter</filter-class>
  <init-param>
    <param-name>role</param-name>
    <param-value>forwarder</param-value>
  </init-param>
</filter>
<filter-mapping>
  <filter-name>baggageFilter</filter-name>
  <url-pattern>/*</url-pattern>
</filter-mapping>
```

## Production safety

- **Build-time**: add under a Maven profile. Production build skips the profile.
- **Runtime**: no-op unless `BAGGAGE_ENABLED=true` env var is set.

## Testing

```bash
mvn clean test
```
