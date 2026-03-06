<?php

declare(strict_types=1);

namespace TektonDag\Baggage\Tests;

use PHPUnit\Framework\TestCase;
use TektonDag\Baggage\W3cBaggageCodec;

final class W3cBaggageCodecTest extends TestCase
{
    public function testParseNullAndEmpty(): void
    {
        $this->assertSame([], W3cBaggageCodec::parse(null));
        $this->assertSame([], W3cBaggageCodec::parse(''));
        $this->assertSame([], W3cBaggageCodec::parse('  '));
    }

    public function testParseSingleEntry(): void
    {
        $result = W3cBaggageCodec::parse('dev-session=abc123');
        $this->assertSame(['dev-session' => 'abc123'], $result);
    }

    public function testParseMultipleEntries(): void
    {
        $result = W3cBaggageCodec::parse('k1=v1,k2=v2,k3=v3');
        $this->assertCount(3, $result);
        $this->assertSame('v1', $result['k1']);
    }

    public function testParsePreservesProperties(): void
    {
        $result = W3cBaggageCodec::parse('k1=v1;prop=pval,k2=v2');
        $this->assertSame('v1;prop=pval', $result['k1']);
    }

    public function testMergeAddsEntry(): void
    {
        $result = W3cBaggageCodec::merge('k1=v1', 'dev-session', 'abc');
        $this->assertStringContainsString('k1=v1', $result);
        $this->assertStringContainsString('dev-session=abc', $result);
    }

    public function testMergeReplacesEntry(): void
    {
        $result = W3cBaggageCodec::merge('dev-session=old,k1=v1', 'dev-session', 'new');
        $this->assertStringContainsString('dev-session=new', $result);
        $this->assertStringNotContainsString('=old', $result);
    }

    public function testMergeOnNull(): void
    {
        $this->assertSame('dev-session=abc', W3cBaggageCodec::merge(null, 'dev-session', 'abc'));
    }

    public function testRoundTrip(): void
    {
        $original = 'k1=v1,k2=v2';
        $parsed = W3cBaggageCodec::parse($original);
        $this->assertSame($original, W3cBaggageCodec::serialize($parsed));
    }
}
