package com.tektondag.baggage;

/** Canonical override-header rules shared with the Spring Boot starter. */
public final class BaggagePolicy {

  private BaggagePolicy() {}

  public static String firstNonBlank(String... values) {
    if (values == null) {
      return null;
    }
    for (String raw : values) {
      if (raw != null && !raw.isBlank()) {
        return raw.trim();
      }
    }
    return null;
  }

  public static String incomingSession(
      BaggageRole role, String header, String cookie, String query, String sessionValue) {
    if (role == null || role == BaggageRole.UNKNOWN) {
      return null;
    }
    String incoming = firstNonBlank(header, cookie, query);
    return switch (role) {
      case ORIGINATOR -> firstNonBlank(incoming, sessionValue);
      case FORWARDER, TERMINAL -> incoming;
      default -> null;
    };
  }

  public static String outgoingSession(
      BaggageRole role, String contextValue, String sessionValue) {
    if (role == null) {
      return null;
    }
    return switch (role) {
      case ORIGINATOR -> firstNonBlank(contextValue, sessionValue);
      case FORWARDER -> firstNonBlank(contextValue);
      default -> null;
    };
  }
}
