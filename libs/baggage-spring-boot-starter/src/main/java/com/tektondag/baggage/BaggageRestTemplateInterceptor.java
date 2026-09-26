package com.tektondag.baggage;

import java.io.IOException;
import org.springframework.http.HttpRequest;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;

/**
 * Outgoing interceptor. Copies the original override header onto RestTemplate
 * calls. Originator mints only when no incoming session is in context.
 */
public class BaggageRestTemplateInterceptor implements ClientHttpRequestInterceptor {

  private final BaggageProperties properties;

  public BaggageRestTemplateInterceptor(BaggageProperties properties) {
    this.properties = properties;
  }

  @Override
  public ClientHttpResponse intercept(
      HttpRequest request, byte[] body, ClientHttpRequestExecution execution) throws IOException {
    BaggagePropagator.apply(request.getHeaders(), properties);
    return execution.execute(request, body);
  }
}
