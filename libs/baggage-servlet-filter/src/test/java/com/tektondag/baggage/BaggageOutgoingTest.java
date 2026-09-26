package com.tektondag.baggage;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import java.util.LinkedHashMap;
import java.util.Map;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

class BaggageOutgoingTest {

  @AfterEach
  void cleanup() {
    BaggageContextHolder.clear();
  }

  @Test
  void copiesOriginalOverrideFromContext() {
    BaggageContextHolder.set("pr-42");
    Map<String, String> headers = new LinkedHashMap<>();
    BaggageOutgoing.apply(headers, "x-dev-session", "dev-session", BaggageRole.FORWARDER, "minted");
    assertEquals("pr-42", headers.get("x-dev-session"));
    assertEquals("dev-session=pr-42", headers.get("baggage"));
  }

  @Test
  void terminalDoesNotWrite() {
    BaggageContextHolder.set("pr-42");
    Map<String, String> headers = new LinkedHashMap<>();
    BaggageOutgoing.apply(headers, "x-dev-session", "dev-session", BaggageRole.TERMINAL, "minted");
    assertFalse(headers.containsKey("x-dev-session"));
  }
}
