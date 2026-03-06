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
    Map<String, String> result = W3cBaggageCodec.parse("key1=val1,key2=val2,key3=val3");
    assertEquals(3, result.size());
    assertEquals("val1", result.get("key1"));
    assertEquals("val2", result.get("key2"));
    assertEquals("val3", result.get("key3"));
  }

  @Test
  void parsePreservesEntryProperties() {
    Map<String, String> result = W3cBaggageCodec.parse("key1=val1;prop1=pval1,key2=val2");
    assertEquals(2, result.size());
    assertEquals("val1;prop1=pval1", result.get("key1"));
    assertEquals("val2", result.get("key2"));
  }

  @Test
  void mergeAddsNewEntry() {
    String result = W3cBaggageCodec.merge("key1=val1", "dev-session", "abc");
    assertTrue(result.contains("key1=val1"));
    assertTrue(result.contains("dev-session=abc"));
  }

  @Test
  void mergeReplacesExistingEntry() {
    String result = W3cBaggageCodec.merge("dev-session=old,key1=val1", "dev-session", "new");
    assertTrue(result.contains("dev-session=new"));
    assertTrue(result.contains("key1=val1"));
    assertFalse(result.contains("=old"));
  }

  @Test
  void mergeOnNullHeader() {
    assertEquals("dev-session=abc", W3cBaggageCodec.merge(null, "dev-session", "abc"));
  }

  @Test
  void serializeRoundTrip() {
    String original = "key1=val1,key2=val2";
    Map<String, String> parsed = W3cBaggageCodec.parse(original);
    assertEquals(original, W3cBaggageCodec.serialize(parsed));
  }
}
