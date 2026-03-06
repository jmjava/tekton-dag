<?php

declare(strict_types=1);

namespace TektonDag\Baggage;

use Psr\Http\Message\RequestInterface;

/**
 * Guzzle middleware that propagates baggage headers on outgoing requests.
 *
 * Usage:
 *   $stack = HandlerStack::create();
 *   $stack->push(GuzzleMiddleware::create());
 *   $client = new Client(['handler' => $stack]);
 */
final class GuzzleMiddleware
{
    public static function create(
        string $role = 'forwarder',
        string $headerName = 'x-dev-session',
        string $baggageKey = 'dev-session',
        string $sessionValue = '',
    ): callable {
        $role = strtolower($role);

        return static function (callable $handler) use ($role, $headerName, $baggageKey, $sessionValue): callable {
            return static function (RequestInterface $request, array $options) use ($handler, $role, $headerName, $baggageKey, $sessionValue) {
                $value = match ($role) {
                    'originator' => self::nonBlank($sessionValue),
                    'forwarder' => BaggageContext::get(),
                    default => null,
                };

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

    private static function nonBlank(?string $s): ?string
    {
        if ($s === null || trim($s) === '') {
            return null;
        }
        return trim($s);
    }
}
