package com.tektondag.baggage;

import java.io.IOException;
import org.springframework.http.HttpRequest;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;

/**
 * Outgoing interceptor that propagates the dev-session header and W3C baggage
 * on RestTemplate calls. Behavior depends on the configured role:
 *   ORIGINATOR — always sets headers from configured session value
 *   FORWARDER  — propagates from ThreadLocal context (set by the incoming filter)
 *   TERMINAL   — no-op (never propagates outgoing)
 */
public class BaggageRestTemplateInterceptor implements ClientHttpRequestInterceptor {

  private final BaggageProperties properties;

  public BaggageRestTemplateInterceptor(BaggageProperties properties) {
    this.properties = properties;
  }

  @Override
  public ClientHttpResponse intercept(
      HttpRequest request,
      byte[] body,
      ClientHttpRequestExecution execution)
      throws IOException {

    String sessionValue = resolveOutgoingValue();
    if (sessionValue != null && !sessionValue.isBlank()) {
      request.getHeaders().set(properties.getHeaderName(), sessionValue);

      String existingBaggage = request.getHeaders().getFirst("baggage");
      String merged =
          W3cBaggageCodec.merge(existingBaggage, properties.getBaggageKey(), sessionValue);
      request.getHeaders().set("baggage", merged);
    }

    return execution.execute(request, body);
  }

  private String resolveOutgoingValue() {
    return switch (properties.getRole()) {
      case ORIGINATOR -> {
        String configured = properties.getSessionValue();
        yield (configured != null && !configured.isBlank()) ? configured.trim() : null;
      }
      case FORWARDER -> BaggageContextHolder.get();
      case TERMINAL -> null;
    };
  }
}
