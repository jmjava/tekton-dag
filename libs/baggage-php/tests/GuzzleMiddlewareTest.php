<?php

declare(strict_types=1);

namespace TektonDag\Baggage\Tests;

use GuzzleHttp\Client;
use GuzzleHttp\Handler\MockHandler;
use GuzzleHttp\HandlerStack;
use GuzzleHttp\Middleware;
use GuzzleHttp\Psr7\Response;
use PHPUnit\Framework\TestCase;
use TektonDag\Baggage\BaggageContext;
use TektonDag\Baggage\GuzzleMiddleware;

final class GuzzleMiddlewareTest extends TestCase
{
    protected function tearDown(): void
    {
        BaggageContext::clear();
    }

    public function testOriginatorSetsHeaders(): void
    {
        $history = [];
        $stack = HandlerStack::create(new MockHandler([new Response(200)]));
        $stack->push(GuzzleMiddleware::create(
            role: 'originator',
            sessionValue: 'orig-sess',
        ));
        $stack->push(Middleware::history($history));

        $client = new Client(['handler' => $stack]);
        $client->get('http://downstream/api');

        $request = $history[0]['request'];
        $this->assertSame('orig-sess', $request->getHeaderLine('x-dev-session'));
        $this->assertStringContainsString('dev-session=orig-sess', $request->getHeaderLine('baggage'));
    }

    public function testForwarderPropagatesFromContext(): void
    {
        BaggageContext::set('fwd-sess');

        $history = [];
        $stack = HandlerStack::create(new MockHandler([new Response(200)]));
        $stack->push(GuzzleMiddleware::create(role: 'forwarder'));
        $stack->push(Middleware::history($history));

        $client = new Client(['handler' => $stack]);
        $client->get('http://downstream/api');

        $request = $history[0]['request'];
        $this->assertSame('fwd-sess', $request->getHeaderLine('x-dev-session'));
    }

    public function testForwarderNoOpWhenContextEmpty(): void
    {
        $history = [];
        $stack = HandlerStack::create(new MockHandler([new Response(200)]));
        $stack->push(GuzzleMiddleware::create(role: 'forwarder'));
        $stack->push(Middleware::history($history));

        $client = new Client(['handler' => $stack]);
        $client->get('http://downstream/api');

        $request = $history[0]['request'];
        $this->assertFalse($request->hasHeader('x-dev-session'));
    }

    public function testTerminalNeverSetsHeaders(): void
    {
        BaggageContext::set('should-not-propagate');

        $history = [];
        $stack = HandlerStack::create(new MockHandler([new Response(200)]));
        $stack->push(GuzzleMiddleware::create(role: 'terminal'));
        $stack->push(Middleware::history($history));

        $client = new Client(['handler' => $stack]);
        $client->get('http://downstream/api');

        $request = $history[0]['request'];
        $this->assertFalse($request->hasHeader('x-dev-session'));
    }
}
