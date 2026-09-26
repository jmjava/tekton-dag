package com.tektondag.baggage;

import org.springframework.http.HttpHeaders;

/**
 * Apply the original override header + W3C baggage onto any outgoing client.
 */
public final class BaggagePropagator {

  private BaggagePropagator() {}

  public static void apply(HttpHeaders headers, BaggageProperties properties) {
    if (headers == null || properties == null) {
      return;
    }
    String value =
        BaggagePolicy.outgoingSession(
            properties.getRole(),
            BaggageContextHolder.get(),
            properties.getSessionValue());
    if (value == null) {
      return;
    }
    headers.set(properties.getHeaderName(), value);
    headers.set(
        "baggage",
        W3cBaggageCodec.merge(headers.getFirst("baggage"), properties.getBaggageKey(), value));
  }
}
