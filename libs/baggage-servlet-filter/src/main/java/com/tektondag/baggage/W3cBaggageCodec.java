package com.tektondag.baggage;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.stream.Collectors;

public final class W3cBaggageCodec {

  private W3cBaggageCodec() {}

  public static Map<String, String> parse(String header) {
    Map<String, String> entries = new LinkedHashMap<>();
    if (header == null || header.isBlank()) {
      return entries;
    }
    for (String member : header.split(",")) {
      String trimmed = member.trim();
      if (trimmed.isEmpty()) continue;
      int eq = trimmed.indexOf('=');
      if (eq < 1) continue;
      String key = trimmed.substring(0, eq).trim();
      String value = trimmed.substring(eq + 1).trim();
      entries.put(key, value);
    }
    return entries;
  }

  public static String merge(String existingHeader, String key, String value) {
    Map<String, String> entries = parse(existingHeader);
    entries.put(key, value);
    return serialize(entries);
  }

  public static String serialize(Map<String, String> entries) {
    return entries.entrySet().stream()
        .map(e -> e.getKey() + "=" + e.getValue())
        .collect(Collectors.joining(","));
  }
}
