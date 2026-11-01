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

  static boolean refusesPropagation(String value) {
    if (value == null) {
      return false;
    }
    for (int i = 0; i < value.length(); i++) {
      char ch = value.charAt(i);
      if (ch < 32 || ch == 127) {
        return true;
      }
    }
    return false;
  }

  static String propagated(String value) {
    if (value == null || refusesPropagation(value)) {
      return null;
    }
    return value;
  }

  public static String incomingSession(
      BaggageRole role, String header, String cookie, String query, String sessionValue) {
    if (role == null || role == BaggageRole.UNKNOWN) {
      return null;
    }
    String incoming = firstNonBlank(header, cookie, query);
    if (refusesPropagation(incoming)) {
      return null;
    }
    return switch (role) {
      case ORIGINATOR -> propagated(firstNonBlank(incoming, sessionValue));
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
      case ORIGINATOR -> propagated(firstNonBlank(contextValue, sessionValue));
      case FORWARDER -> propagated(firstNonBlank(contextValue));
      default -> null;
    };
  }
}
