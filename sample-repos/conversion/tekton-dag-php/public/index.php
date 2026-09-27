<?php
require_once dirname(__DIR__) . '/vendor/autoload.php';

use TektonDag\Baggage\Baggage;
use TektonDag\Baggage\BaggageContext;

Baggage::install();

$hops = [];
$downstream = getenv('DOWNSTREAM_URL') ?: '';
if ($downstream !== '') {
    try {
        $client = Baggage::guzzleClient(['timeout' => 10]);
        $response = $client->get(rtrim($downstream, '/') . '/propagation');
        $decoded = json_decode((string) $response->getBody(), true);
        if (is_array($decoded)) {
            $hops[] = $decoded;
        }
    } catch (Throwable $e) {
        $hops[] = ['error' => $e->getMessage()];
    }
}

header('Content-Type: application/json');
echo json_encode([
    'app' => getenv('APP_NAME') ?: 'tekton-dag-php',
    'session' => BaggageContext::get(),
    'hops' => $hops,
], JSON_UNESCAPED_SLASHES);
