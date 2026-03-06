package com.tektondag.baggage;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

import java.net.URI;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.mock.http.client.MockClientHttpRequest;

class BaggageRestTemplateInterceptorTest {

  private static final byte[] EMPTY = new byte[0];

  @AfterEach
  void cleanup() {
    BaggageContextHolder.clear();
  }

  @Test
  void originatorSetsHeaders() throws Exception {
    BaggageProperties props = new BaggageProperties();
    props.setRole(BaggageRole.ORIGINATOR);
    props.setSessionValue("orig-session");

    var interceptor = new BaggageRestTemplateInterceptor(props);
    var request = new MockClientHttpRequest(HttpMethod.GET, URI.create("http://downstream/api"));
    var execution = mockExecution();

    interceptor.intercept(request, EMPTY, execution);

    assertEquals("orig-session", request.getHeaders().getFirst("x-dev-session"));
    assertEquals("dev-session=orig-session", request.getHeaders().getFirst("baggage"));
  }

  @Test
  void forwarderPropagatesFromContext() throws Exception {
    BaggageProperties props = new BaggageProperties();
    props.setRole(BaggageRole.FORWARDER);
    BaggageContextHolder.set("forwarded-session");

    var interceptor = new BaggageRestTemplateInterceptor(props);
    var request = new MockClientHttpRequest(HttpMethod.GET, URI.create("http://downstream/api"));
    var execution = mockExecution();

    interceptor.intercept(request, EMPTY, execution);

    assertEquals("forwarded-session", request.getHeaders().getFirst("x-dev-session"));
    assertTrue(request.getHeaders().getFirst("baggage").contains("dev-session=forwarded-session"));
  }

  @Test
  void forwarderNoOpWhenContextEmpty() throws Exception {
    BaggageProperties props = new BaggageProperties();
    props.setRole(BaggageRole.FORWARDER);

    var interceptor = new BaggageRestTemplateInterceptor(props);
    var request = new MockClientHttpRequest(HttpMethod.GET, URI.create("http://downstream/api"));
    var execution = mockExecution();

    interceptor.intercept(request, EMPTY, execution);

    assertNull(request.getHeaders().getFirst("x-dev-session"));
    assertNull(request.getHeaders().getFirst("baggage"));
  }

  @Test
  void terminalNeverSetsHeaders() throws Exception {
    BaggageProperties props = new BaggageProperties();
    props.setRole(BaggageRole.TERMINAL);
    BaggageContextHolder.set("should-not-propagate");

    var interceptor = new BaggageRestTemplateInterceptor(props);
    var request = new MockClientHttpRequest(HttpMethod.GET, URI.create("http://downstream/api"));
    var execution = mockExecution();

    interceptor.intercept(request, EMPTY, execution);

    assertNull(request.getHeaders().getFirst("x-dev-session"));
    assertNull(request.getHeaders().getFirst("baggage"));
  }

  @Test
  void mergesWithExistingBaggageHeader() throws Exception {
    BaggageProperties props = new BaggageProperties();
    props.setRole(BaggageRole.ORIGINATOR);
    props.setSessionValue("my-session");

    var interceptor = new BaggageRestTemplateInterceptor(props);
    var request = new MockClientHttpRequest(HttpMethod.GET, URI.create("http://downstream/api"));
    request.getHeaders().set("baggage", "traceId=abc123,spanId=def456");
    var execution = mockExecution();

    interceptor.intercept(request, EMPTY, execution);

    String baggage = request.getHeaders().getFirst("baggage");
    assertTrue(baggage.contains("traceId=abc123"));
    assertTrue(baggage.contains("spanId=def456"));
    assertTrue(baggage.contains("dev-session=my-session"));
  }

  private static ClientHttpRequestExecution mockExecution() throws Exception {
    ClientHttpRequestExecution exec = mock(ClientHttpRequestExecution.class);
    when(exec.execute(any(), any())).thenReturn(mock(ClientHttpResponse.class));
    return exec;
  }
}
