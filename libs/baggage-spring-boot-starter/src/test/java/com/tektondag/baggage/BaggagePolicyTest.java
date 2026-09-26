package com.tektondag.baggage;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import org.junit.jupiter.api.Test;

class BaggagePolicyTest {

  @Test
  void originatorPreservesOriginalOverrideHeader() {
    assertEquals(
        "pr-42",
        BaggagePolicy.incomingSession(
            BaggageRole.ORIGINATOR, "pr-42", null, null, "minted"));
  }

  @Test
  void originatorMintsOnlyWhenNothingIncoming() {
    assertEquals(
        "minted",
        BaggagePolicy.incomingSession(BaggageRole.ORIGINATOR, null, null, null, "minted"));
  }

  @Test
  void originatorCookieBeforeSessionValue() {
    assertEquals(
        "from-cookie",
        BaggagePolicy.incomingSession(
            BaggageRole.ORIGINATOR, null, "from-cookie", "from-query", "minted"));
  }

  @Test
  void forwarderDoesNotMint() {
    assertNull(
        BaggagePolicy.incomingSession(
            BaggageRole.FORWARDER, null, null, null, "must-not-mint"));
  }

  @Test
  void unknownRoleFailClosed() {
    assertNull(
        BaggagePolicy.incomingSession(BaggageRole.UNKNOWN, "pr-42", null, null, "minted"));
    assertNull(BaggagePolicy.outgoingSession(BaggageRole.UNKNOWN, "pr-42", "minted"));
  }

  @Test
  void outgoingNeverRewritesContext() {
    assertEquals(
        "pr-42",
        BaggagePolicy.outgoingSession(BaggageRole.ORIGINATOR, "pr-42", "minted"));
    assertEquals(
        "pr-42", BaggagePolicy.outgoingSession(BaggageRole.FORWARDER, "pr-42", "minted"));
    assertNull(BaggagePolicy.outgoingSession(BaggageRole.TERMINAL, "pr-42", "minted"));
  }
}
