# baggage-spring-boot-starter

Role-aware W3C baggage / `x-dev-session` auto-configuration for Spring Boot.

## Installation

```xml
<dependency>
  <groupId>com.tektondag</groupId>
  <artifactId>baggage-spring-boot-starter</artifactId>
  <version>1.0.0</version>
</dependency>
```

Install locally first: `cd libs/baggage-spring-boot-starter && mvn install`

## Configuration (application.properties)

| Property | Default | Description |
|----------|---------|-------------|
| `baggage.enabled` | `false` | Must be `true` to activate |
| `baggage.role` | `FORWARDER` | `ORIGINATOR`, `FORWARDER`, or `TERMINAL` |
| `baggage.header-name` | `x-dev-session` | Custom header name |
| `baggage.baggage-key` | `dev-session` | W3C baggage key |
| `baggage.session-value` | (empty) | Session value for originator role |

## Usage

Add the dependency. Spring Boot auto-configuration handles the rest. Set `baggage.enabled=true` and `baggage.role` in your application.properties.

## Production safety

- **Build-time**: add under a Maven profile. Production build skips the profile.
- **Runtime**: `@ConditionalOnProperty(name = "baggage.enabled", havingValue = "true")`.

## Testing

```bash
mvn clean test
```
