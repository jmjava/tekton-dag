package com.tektondag.baggage;

import java.net.URLConnection;
import java.util.Map;

/**
 * Apply the original override header onto any outgoing client. Use this
 * instead of copying headers by hand.
 */
public final class BaggageOutgoing {

  private BaggageOutgoing() {}

  public static void apply(
      Map<String, String> headers,
      String headerName,
      String baggageKey,
      BaggageRole role,
      String sessionValue) {
    if (headers == null) {
      return;
    }
    String value = BaggagePolicy.outgoingSession(role, BaggageContextHolder.get(), sessionValue);
    if (value == null) {
      return;
    }
    headers.put(headerName, value);
    headers.put("baggage", W3cBaggageCodec.merge(headers.get("baggage"), baggageKey, value));
  }

  public static void apply(URLConnection connection, String headerName, String baggageKey, BaggageRole role, String sessionValue) {
    if (connection == null) {
      return;
    }
    String value = BaggagePolicy.outgoingSession(role, BaggageContextHolder.get(), sessionValue);
    if (value == null) {
      return;
    }
    connection.setRequestProperty(headerName, value);
    String existing = connection.getRequestProperty("baggage");
    connection.setRequestProperty("baggage", W3cBaggageCodec.merge(existing, baggageKey, value));
  }
}
