package com.tektondag.baggage;

public enum BaggageRole {
  ORIGINATOR,
  FORWARDER,
  TERMINAL;

  public static BaggageRole fromString(String s) {
    if (s == null) return FORWARDER;
    return switch (s.trim().toUpperCase()) {
      case "ORIGINATOR" -> ORIGINATOR;
      case "TERMINAL" -> TERMINAL;
      default -> FORWARDER;
    };
  }
}
