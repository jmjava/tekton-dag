<?php

declare(strict_types=1);

namespace TektonDag\Baggage;

final class W3cBaggageCodec
{
    /** @return array<string, string> */
    public static function parse(?string $header): array
    {
        $entries = [];
        if ($header === null || trim($header) === '') {
            return $entries;
        }
        foreach (explode(',', $header) as $member) {
            $member = trim($member);
            if ($member === '') {
                continue;
            }
            $eq = strpos($member, '=');
            if ($eq === false || $eq < 1) {
                continue;
            }
            $key = trim(substr($member, 0, $eq));
            $value = trim(substr($member, $eq + 1));
            $entries[$key] = $value;
        }
        return $entries;
    }

    public static function merge(?string $existingHeader, string $key, string $value): string
    {
        $entries = self::parse($existingHeader);
        $entries[$key] = $value;
        return self::serialize($entries);
    }

    /** @param array<string, string> $entries */
    public static function serialize(array $entries): string
    {
        $parts = [];
        foreach ($entries as $k => $v) {
            $parts[] = "{$k}={$v}";
        }
        return implode(',', $parts);
    }
}
