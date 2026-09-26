<?php

declare(strict_types=1);

namespace TektonDag\Baggage;

use Psr\Http\Message\RequestInterface;

/**
 * Outgoing Guzzle middleware. Copies the original override onto the next hop.
 *
 * Usage:
 *   $client = Baggage::guzzleClient();
 * or:
 *   $stack->push(GuzzleMiddleware::fromEnv());
 */
final class GuzzleMiddleware
{
    public static function fromEnv(): callable
    {
        return self::create(
            role: getenv('BAGGAGE_ROLE') ?: 'forwarder',
            headerName: getenv('BAGGAGE_HEADER_NAME') ?: 'x-dev-session',
            baggageKey: getenv('BAGGAGE_KEY') ?: 'dev-session',
            sessionValue: getenv('BAGGAGE_SESSION_VALUE') ?: '',
        );
    }

    public static function create(
        string $role = 'forwarder',
        string $headerName = 'x-dev-session',
        string $baggageKey = 'dev-session',
        string $sessionValue = '',
    ): callable {
        return static function (callable $handler) use ($role, $headerName, $baggageKey, $sessionValue): callable {
            return static function (RequestInterface $request, array $options) use ($handler, $role, $headerName, $baggageKey, $sessionValue) {
                $value = BaggagePolicy::outgoingSession($role, BaggageContext::get(), $sessionValue);

                if ($value !== null) {
                    $request = $request->withHeader($headerName, $value);
                    $existing = $request->getHeaderLine('baggage');
                    $merged = W3cBaggageCodec::merge(
                        $existing !== '' ? $existing : null,
                        $baggageKey,
                        $value,
                    );
                    $request = $request->withHeader('baggage', $merged);
                }

                return $handler($request, $options);
            };
        };
    }
}
