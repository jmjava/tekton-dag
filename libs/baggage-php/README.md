# tekton-dag/baggage-middleware

Transfers the **original override header** hop-to-hop. Spec: [docs/BAGGAGE-CONTRACT.md](../../docs/BAGGAGE-CONTRACT.md).

```php
use TektonDag\Baggage\Baggage;

Baggage::install();                 // incoming from $_SERVER / cookie / query
$client = Baggage::guzzleClient();  // outgoing copies that same value
```

Do not push a hand-written Guzzle middleware. Originators adopt incoming `pr-42`; they do not overwrite it with `BAGGAGE_SESSION_VALUE`.

```bash
./scripts/emit-baggage-env.sh --stack stacks/stack-one.yaml --app my-php-app
composer install && vendor/bin/phpunit
```
