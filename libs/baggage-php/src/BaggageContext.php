<?php

declare(strict_types=1);

namespace TektonDag\Baggage;

/**
 * Request-scoped context holder for the dev-session value.
 */
final class BaggageContext
{
    private static ?string $value = null;

    public static function set(?string $value): void
    {
        self::$value = $value;
    }

    public static function get(): ?string
    {
        return self::$value;
    }

    public static function clear(): void
    {
        self::$value = null;
    }
}
