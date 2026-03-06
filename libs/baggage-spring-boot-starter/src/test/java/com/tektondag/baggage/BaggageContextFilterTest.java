package com.tektondag.baggage;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import jakarta.servlet.FilterChain;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

class BaggageContextFilterTest {

  @AfterEach
  void cleanup() {
    BaggageContextHolder.clear();
  }

  @Test
  void forwarderExtractsIncomingHeader() throws Exception {
    BaggageProperties props = forwarderProps();
    BaggageContextFilter filter = new BaggageContextFilter(props);

    MockHttpServletRequest request = new MockHttpServletRequest();
    request.addHeader("x-dev-session", "session-abc");
    MockHttpServletResponse response = new MockHttpServletResponse();

    FilterChain chain = mock(FilterChain.class);
    doAnswer(
            inv -> {
              assertEquals("session-abc", BaggageContextHolder.get());
              return null;
            })
        .when(chain)
        .doFilter(request, response);

    filter.doFilterInternal(request, response, chain);

    verify(chain).doFilter(request, response);
    assertNull(BaggageContextHolder.get(), "ThreadLocal must be cleared after filter completes");
  }

  @Test
  void forwarderNoOpWhenHeaderMissing() throws Exception {
    BaggageContextFilter filter = new BaggageContextFilter(forwarderProps());

    MockHttpServletRequest request = new MockHttpServletRequest();
    MockHttpServletResponse response = new MockHttpServletResponse();
    FilterChain chain = mock(FilterChain.class);

    filter.doFilterInternal(request, response, chain);

    verify(chain).doFilter(request, response);
    assertNull(BaggageContextHolder.get());
  }

  @Test
  void originatorUsesConfiguredValue() throws Exception {
    BaggageProperties props = originatorProps("my-dev-session");
    BaggageContextFilter filter = new BaggageContextFilter(props);

    MockHttpServletRequest request = new MockHttpServletRequest();
    MockHttpServletResponse response = new MockHttpServletResponse();

    FilterChain chain = mock(FilterChain.class);
    doAnswer(
            inv -> {
              assertEquals("my-dev-session", BaggageContextHolder.get());
              return null;
            })
        .when(chain)
        .doFilter(request, response);

    filter.doFilterInternal(request, response, chain);
    verify(chain).doFilter(request, response);
  }

  @Test
  void originatorIgnoresIncomingHeader() throws Exception {
    BaggageProperties props = originatorProps("configured-value");
    BaggageContextFilter filter = new BaggageContextFilter(props);

    MockHttpServletRequest request = new MockHttpServletRequest();
    request.addHeader("x-dev-session", "should-be-ignored");
    MockHttpServletResponse response = new MockHttpServletResponse();

    FilterChain chain = mock(FilterChain.class);
    doAnswer(
            inv -> {
              assertEquals("configured-value", BaggageContextHolder.get());
              return null;
            })
        .when(chain)
        .doFilter(request, response);

    filter.doFilterInternal(request, response, chain);
  }

  @Test
  void terminalExtractsHeader() throws Exception {
    BaggageProperties props = terminalProps();
    BaggageContextFilter filter = new BaggageContextFilter(props);

    MockHttpServletRequest request = new MockHttpServletRequest();
    request.addHeader("x-dev-session", "terminal-session");
    MockHttpServletResponse response = new MockHttpServletResponse();

    FilterChain chain = mock(FilterChain.class);
    doAnswer(
            inv -> {
              assertEquals("terminal-session", BaggageContextHolder.get());
              return null;
            })
        .when(chain)
        .doFilter(request, response);

    filter.doFilterInternal(request, response, chain);
    assertNull(BaggageContextHolder.get(), "ThreadLocal must be cleared after filter completes");
  }

  // --- helpers ---

  private static BaggageProperties forwarderProps() {
    BaggageProperties p = new BaggageProperties();
    p.setEnabled(true);
    p.setRole(BaggageRole.FORWARDER);
    return p;
  }

  private static BaggageProperties originatorProps(String sessionValue) {
    BaggageProperties p = new BaggageProperties();
    p.setEnabled(true);
    p.setRole(BaggageRole.ORIGINATOR);
    p.setSessionValue(sessionValue);
    return p;
  }

  private static BaggageProperties terminalProps() {
    BaggageProperties p = new BaggageProperties();
    p.setEnabled(true);
    p.setRole(BaggageRole.TERMINAL);
    return p;
  }
}
