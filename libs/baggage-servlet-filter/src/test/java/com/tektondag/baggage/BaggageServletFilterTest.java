package com.tektondag.baggage;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import javax.servlet.FilterChain;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

class BaggageServletFilterTest {

  @AfterEach
  void cleanup() {
    BaggageContextHolder.clear();
  }

  @Test
  void forwarderExtractsHeader() throws Exception {
    BaggageServletFilter filter = enabledFilter(BaggageRole.FORWARDER);
    HttpServletRequest req = mockRequest("x-dev-session", "sess-1");
    HttpServletResponse resp = mock(HttpServletResponse.class);

    FilterChain chain = mock(FilterChain.class);
    doAnswer(inv -> {
      assertEquals("sess-1", BaggageContextHolder.get());
      return null;
    }).when(chain).doFilter(req, resp);

    filter.doFilter(req, resp, chain);
    verify(chain).doFilter(req, resp);
    assertNull(BaggageContextHolder.get());
  }

  @Test
  void forwarderNoOpWhenHeaderMissing() throws Exception {
    BaggageServletFilter filter = enabledFilter(BaggageRole.FORWARDER);
    HttpServletRequest req = mockRequest("x-dev-session", null);
    HttpServletResponse resp = mock(HttpServletResponse.class);
    FilterChain chain = mock(FilterChain.class);

    filter.doFilter(req, resp, chain);
    verify(chain).doFilter(req, resp);
    assertNull(BaggageContextHolder.get());
  }

  @Test
  void originatorUsesConfiguredValue() throws Exception {
    BaggageServletFilter filter = enabledFilter(BaggageRole.ORIGINATOR);
    filter.setSessionValue("my-session");
    HttpServletRequest req = mockRequest("x-dev-session", null);
    HttpServletResponse resp = mock(HttpServletResponse.class);

    FilterChain chain = mock(FilterChain.class);
    doAnswer(inv -> {
      assertEquals("my-session", BaggageContextHolder.get());
      return null;
    }).when(chain).doFilter(req, resp);

    filter.doFilter(req, resp, chain);
    verify(chain).doFilter(req, resp);
  }

  @Test
  void originatorIgnoresIncomingHeader() throws Exception {
    BaggageServletFilter filter = enabledFilter(BaggageRole.ORIGINATOR);
    filter.setSessionValue("configured");
    HttpServletRequest req = mockRequest("x-dev-session", "should-ignore");
    HttpServletResponse resp = mock(HttpServletResponse.class);

    FilterChain chain = mock(FilterChain.class);
    doAnswer(inv -> {
      assertEquals("configured", BaggageContextHolder.get());
      return null;
    }).when(chain).doFilter(req, resp);

    filter.doFilter(req, resp, chain);
  }

  @Test
  void terminalExtractsHeader() throws Exception {
    BaggageServletFilter filter = enabledFilter(BaggageRole.TERMINAL);
    HttpServletRequest req = mockRequest("x-dev-session", "term-val");
    HttpServletResponse resp = mock(HttpServletResponse.class);

    FilterChain chain = mock(FilterChain.class);
    doAnswer(inv -> {
      assertEquals("term-val", BaggageContextHolder.get());
      return null;
    }).when(chain).doFilter(req, resp);

    filter.doFilter(req, resp, chain);
    assertNull(BaggageContextHolder.get());
  }

  @Test
  void productionGuardBlocksWhenDisabled() throws Exception {
    BaggageServletFilter filter = new BaggageServletFilter();
    filter.setRole(BaggageRole.FORWARDER);
    filter.setEnabledOverride(false);

    HttpServletRequest req = mockRequest("x-dev-session", "should-not-extract");
    HttpServletResponse resp = mock(HttpServletResponse.class);
    FilterChain chain = mock(FilterChain.class);

    filter.doFilter(req, resp, chain);
    verify(chain).doFilter(req, resp);
    assertNull(BaggageContextHolder.get());
  }

  // --- helpers ---

  private static BaggageServletFilter enabledFilter(BaggageRole role) {
    BaggageServletFilter filter = new BaggageServletFilter();
    filter.setRole(role);
    filter.setEnabledOverride(true);
    return filter;
  }

  private static HttpServletRequest mockRequest(String headerName, String headerValue) {
    HttpServletRequest req = mock(HttpServletRequest.class);
    when(req.getHeader(headerName)).thenReturn(headerValue);
    return req;
  }
}
