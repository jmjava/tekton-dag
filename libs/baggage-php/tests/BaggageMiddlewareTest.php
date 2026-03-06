<?php

declare(strict_types=1);

namespace TektonDag\Baggage\Tests;

use PHPUnit\Framework\TestCase;
use TektonDag\Baggage\BaggageContext;
use TektonDag\Baggage\BaggageMiddleware;

final class BaggageMiddlewareTest extends TestCase
{
    protected function tearDown(): void
    {
        BaggageContext::clear();
        putenv('BAGGAGE_ENABLED');
        putenv('BAGGAGE_ROLE');
        putenv('BAGGAGE_SESSION_VALUE');
    }

    public function testForwarderExtractsHeader(): void
    {
        putenv('BAGGAGE_ENABLED=true');
        $mw = new BaggageMiddleware(role: 'forwarder');
        $mw->handle('session-abc');
        $this->assertSame('session-abc', BaggageContext::get());
    }

    public function testForwarderNoOpWhenHeaderMissing(): void
    {
        putenv('BAGGAGE_ENABLED=true');
        $mw = new BaggageMiddleware(role: 'forwarder');
        $mw->handle(null);
        $this->assertNull(BaggageContext::get());
    }

    public function testOriginatorUsesConfiguredValue(): void
    {
        putenv('BAGGAGE_ENABLED=true');
        $mw = new BaggageMiddleware(role: 'originator', sessionValue: 'my-session');
        $mw->handle(null);
        $this->assertSame('my-session', BaggageContext::get());
    }

    public function testOriginatorIgnoresIncomingHeader(): void
    {
        putenv('BAGGAGE_ENABLED=true');
        $mw = new BaggageMiddleware(role: 'originator', sessionValue: 'configured');
        $mw->handle('should-be-ignored');
        $this->assertSame('configured', BaggageContext::get());
    }

    public function testTerminalExtractsHeader(): void
    {
        putenv('BAGGAGE_ENABLED=true');
        $mw = new BaggageMiddleware(role: 'terminal');
        $mw->handle('term-val');
        $this->assertSame('term-val', BaggageContext::get());
    }

    public function testProductionGuardDisabled(): void
    {
        putenv('BAGGAGE_ENABLED=false');
        $mw = new BaggageMiddleware(role: 'forwarder');
        $result = $mw->handle('should-not-extract');
        $this->assertFalse($result);
        $this->assertNull(BaggageContext::get());
    }

    public function testProductionGuardMissingEnv(): void
    {
        putenv('BAGGAGE_ENABLED');
        $mw = new BaggageMiddleware(role: 'forwarder');
        $result = $mw->handle('nope');
        $this->assertFalse($result);
        $this->assertNull(BaggageContext::get());
    }
}
