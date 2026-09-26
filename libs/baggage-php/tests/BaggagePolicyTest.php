<?php

declare(strict_types=1);

namespace TektonDag\Baggage\Tests;

use PHPUnit\Framework\TestCase;
use TektonDag\Baggage\BaggagePolicy;

final class BaggagePolicyTest extends TestCase
{
    /** @return array<string, mixed> */
    private function vectors(): array
    {
        $path = dirname(__DIR__, 2) . '/baggage-contract/vectors.json';
        $decoded = json_decode((string) file_get_contents($path), true);
        $this->assertIsArray($decoded);
        return $decoded;
    }

    public function testIncomingVectorsPreserveOriginalOverride(): void
    {
        foreach ($this->vectors()['resolveIncoming'] as $case) {
            $got = BaggagePolicy::incomingSession(
                $case['role'] ?? null,
                $case['header'] ?? null,
                $case['cookie'] ?? null,
                $case['query'] ?? null,
                $case['sessionValue'] ?? null,
                $case['enabled'] ?? true,
            );
            $this->assertSame($case['expected'], $got, $case['name']);
        }
    }

    public function testOutgoingVectorsNeverRewrite(): void
    {
        foreach ($this->vectors()['resolveOutgoing'] as $case) {
            $got = BaggagePolicy::outgoingSession(
                $case['role'] ?? null,
                $case['context'] ?? null,
                $case['sessionValue'] ?? null,
            );
            $this->assertSame($case['expected'], $got, $case['name']);
        }
    }
}
