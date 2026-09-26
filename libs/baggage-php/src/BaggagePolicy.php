<?php

declare(strict_types=1);

namespace TektonDag\Baggage;

/**
 * Canonical override-header rules. The incoming session that selects a
 * PR/override container must be copied unchanged onto the next hop.
 */
final class BaggagePolicy
{
    public const ROLES = ['originator', 'forwarder', 'terminal'];

    public static function firstNonBlank(?string ...$values): ?string
    {
        foreach ($values as $raw) {
            if ($raw === null) {
                continue;
            }
            $text = trim($raw);
            if ($text !== '') {
                return $text;
            }
        }
        return null;
    }

    public static function normalizeRole(?string $role): ?string
    {
        if ($role === null || trim($role) === '') {
            return 'forwarder';
        }
        $text = strtolower(trim($role));
        return in_array($text, self::ROLES, true) ? $text : null;
    }

    public static function incomingSession(
        ?string $role,
        ?string $header = null,
        ?string $cookie = null,
        ?string $query = null,
        ?string $sessionValue = null,
        bool $enabled = true,
    ): ?string {
        if (!$enabled) {
            return null;
        }
        $resolved = self::normalizeRole($role);
        if ($resolved === null) {
            return null;
        }
        $incoming = self::firstNonBlank($header, $cookie, $query);
        if ($resolved === 'originator') {
            return self::firstNonBlank($incoming, $sessionValue);
        }
        return $incoming;
    }

    public static function outgoingSession(
        ?string $role,
        ?string $contextValue = null,
        ?string $sessionValue = null,
    ): ?string {
        $resolved = self::normalizeRole($role);
        return match ($resolved) {
            'originator' => self::firstNonBlank($contextValue, $sessionValue),
            'forwarder' => self::firstNonBlank($contextValue),
            default => null,
        };
    }
}
