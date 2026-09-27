<?php

declare(strict_types=1);

namespace TektonDag\Baggage;

/**
 * Incoming request handler. Stores the original override in BaggageContext.
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
     * Extract the original override into BaggageContext.
     * Returns false (no-op) if BAGGAGE_ENABLED is not "true".
     */
    public function handle(
        ?string $incomingHeaderValue = null,
        ?string $cookie = null,
        ?string $query = null,
    ): bool {
        $enabled = strtolower(getenv('BAGGAGE_ENABLED') ?: '') === 'true';
        if (!$enabled) {
            return false;
        }

        $value = BaggagePolicy::incomingSession(
            $this->role,
            $incomingHeaderValue,
            $cookie,
            $query,
            $this->sessionValue,
            true,
        );
        BaggageContext::set($value);
        return true;
    }

    public function handleFromGlobals(): bool
    {
        $serverKey = 'HTTP_' . strtoupper(str_replace('-', '_', $this->headerName));
        $incoming = isset($_SERVER[$serverKey]) ? (string) $_SERVER[$serverKey] : null;
        $cookie = isset($_COOKIE[$this->headerName]) ? (string) $_COOKIE[$this->headerName] : null;
        $query = isset($_GET[$this->headerName]) ? (string) $_GET[$this->headerName] : null;
        return $this->handle($incoming, $cookie, $query);
    }
}
