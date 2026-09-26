package com.tektondag.baggage;

public enum BaggageRole {
  ORIGINATOR,
  FORWARDER,
  TERMINAL,
  UNKNOWN;

  public static BaggageRole fromString(String s) {
    if (s == null || s.isBlank()) {
      return FORWARDER;
    }
    return switch (s.trim().toLowerCase()) {
      case "originator" -> ORIGINATOR;
      case "forwarder" -> FORWARDER;
      case "terminal" -> TERMINAL;
      default -> UNKNOWN;
    };
  }
}
