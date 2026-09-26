<?php

declare(strict_types=1);

namespace TektonDag\Baggage;

use GuzzleHttp\Client;
use GuzzleHttp\HandlerStack;

/**
 * One-call install so apps do not write their own header forwarding.
 */
final class Baggage
{
    public static function install(): bool
    {
        return BaggageMiddleware::fromEnv()->handleFromGlobals();
    }

    public static function guzzleClient(array $config = []): Client
    {
        $stack = HandlerStack::create();
        $stack->push(GuzzleMiddleware::fromEnv());
        $config['handler'] = $stack;
        return new Client($config);
    }
}
