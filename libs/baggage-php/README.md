# tekton-dag/baggage-middleware

Role-aware W3C baggage / `x-dev-session` middleware for PHP (PSR-15 + Guzzle).

## Installation

```bash
composer require tekton-dag/baggage-middleware --dev
# or from local path in composer.json:
# "repositories": [{"type": "path", "url": "/path/to/tekton-dag/libs/baggage-php"}]
```

## Configuration (environment variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `BAGGAGE_ENABLED` | (unset) | Must be `true` to activate |
| `BAGGAGE_ROLE` | `forwarder` | `originator`, `forwarder`, or `terminal` |
| `BAGGAGE_HEADER_NAME` | `x-dev-session` | Custom header name |
| `BAGGAGE_SESSION_VALUE` | (empty) | Session value for originator role |

## Usage

### Incoming (request lifecycle)
```php
use TektonDag\Baggage\BaggageMiddleware;

$middleware = BaggageMiddleware::fromEnv();
$middleware->handleFromGlobals();
```

### Outgoing (Guzzle)
```php
use GuzzleHttp\Client;
use GuzzleHttp\HandlerStack;
use TektonDag\Baggage\GuzzleMiddleware;

$stack = HandlerStack::create();
$stack->push(GuzzleMiddleware::create(role: 'forwarder'));
$client = new Client(['handler' => $stack]);
```

## Production safety

- **Build-time**: `composer require-dev`. Production `composer install --no-dev` excludes it.
- **Runtime**: no-op unless `BAGGAGE_ENABLED=true`.

## Testing

```bash
composer install
vendor/bin/phpunit
```
