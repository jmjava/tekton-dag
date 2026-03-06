<?php

declare(strict_types=1);

namespace TektonDag\Baggage;

/**
 * Role-aware baggage middleware for plain PHP apps.
 *
 * Call BaggageMiddleware::handle() at the top of your request lifecycle.
 * It reads the configured role and extracts or sets the dev-session value
 * into BaggageContext for downstream use.
 *
 * Production safety: no-op unless BAGGAGE_ENABLED=true.
 */
final class BaggageMiddleware
{
    private string $role;
    private string $headerName;
    private string $sessionValue;

    public function __construct(
        string $role = 'forwarder',
        string $headerName = 'x-dev-session',
        string $sessionValue = '',
    ) {
        $this->role = strtolower($role);
        $this->headerName = $headerName;
        $this->sessionValue = $sessionValue;
    }

    public static function fromEnv(): self
    {
        return new self(
            role: getenv('BAGGAGE_ROLE') ?: 'forwarder',
            headerName: getenv('BAGGAGE_HEADER_NAME') ?: 'x-dev-session',
            sessionValue: getenv('BAGGAGE_SESSION_VALUE') ?: '',
        );
    }

    /**
     * Extract or set the session value into BaggageContext.
     * Returns false (no-op) if BAGGAGE_ENABLED is not "true".
     */
    public function handle(?string $incomingHeaderValue = null): bool
    {
        $enabled = strtolower(getenv('BAGGAGE_ENABLED') ?: '') === 'true';
        if (!$enabled) {
            return false;
        }

        $value = $this->resolveValue($incomingHeaderValue);
        BaggageContext::set($value);
        return true;
    }

    /**
     * Convenience: read the header from $_SERVER automatically.
     */
    public function handleFromGlobals(): bool
    {
        $serverKey = 'HTTP_' . strtoupper(str_replace('-', '_', $this->headerName));
        $incoming = $_SERVER[$serverKey] ?? null;
        return $this->handle($incoming);
    }

    private function resolveValue(?string $incomingHeaderValue): ?string
    {
        return match ($this->role) {
            'originator' => $this->nonBlank($this->sessionValue),
            'forwarder', 'terminal' => $this->nonBlank($incomingHeaderValue),
            default => null,
        };
    }

    private function nonBlank(?string $s): ?string
    {
        if ($s === null || trim($s) === '') {
            return null;
        }
        return trim($s);
    }
}
