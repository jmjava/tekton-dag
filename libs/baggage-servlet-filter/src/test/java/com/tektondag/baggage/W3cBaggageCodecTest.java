package com.tektondag.baggage;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Map;
import org.junit.jupiter.api.Test;

class W3cBaggageCodecTest {

  @Test
  void parseNullAndEmpty() {
    assertTrue(W3cBaggageCodec.parse(null).isEmpty());
    assertTrue(W3cBaggageCodec.parse("").isEmpty());
    assertTrue(W3cBaggageCodec.parse("  ").isEmpty());
  }

  @Test
  void parseSingleEntry() {
    Map<String, String> result = W3cBaggageCodec.parse("dev-session=abc123");
    assertEquals(1, result.size());
    assertEquals("abc123", result.get("dev-session"));
  }

  @Test
  void parseMultipleEntries() {
    Map<String, String> result = W3cBaggageCodec.parse("k1=v1,k2=v2,k3=v3");
    assertEquals(3, result.size());
    assertEquals("v1", result.get("k1"));
  }

  @Test
  void mergeAddsEntry() {
    String result = W3cBaggageCodec.merge("k1=v1", "dev-session", "abc");
    assertTrue(result.contains("k1=v1"));
    assertTrue(result.contains("dev-session=abc"));
  }

  @Test
  void mergeReplacesEntry() {
    String result = W3cBaggageCodec.merge("dev-session=old,k1=v1", "dev-session", "new");
    assertTrue(result.contains("dev-session=new"));
    assertFalse(result.contains("=old"));
  }

  @Test
  void mergeOnNull() {
    assertEquals("dev-session=abc", W3cBaggageCodec.merge(null, "dev-session", "abc"));
  }

  @Test
  void roundTrip() {
    String original = "k1=v1,k2=v2";
    assertEquals(original, W3cBaggageCodec.serialize(W3cBaggageCodec.parse(original)));
  }
}
