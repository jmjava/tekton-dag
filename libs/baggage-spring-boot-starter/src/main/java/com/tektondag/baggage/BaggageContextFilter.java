package com.tektondag.baggage;

import io.opentelemetry.api.baggage.Baggage;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.Scope;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Role-aware incoming filter. Extracts or creates a dev-session value,
 * stores it in OTel Baggage and BaggageContextHolder (ThreadLocal)
 * for downstream propagation by BaggageRestTemplateInterceptor.
 */
public class BaggageContextFilter extends OncePerRequestFilter {

  private final BaggageProperties properties;

  public BaggageContextFilter(BaggageProperties properties) {
    this.properties = properties;
  }

  @Override
  protected void doFilterInternal(
      HttpServletRequest request,
      HttpServletResponse response,
      FilterChain filterChain)
      throws ServletException, IOException {

    String sessionValue = resolveSessionValue(request);

    if (sessionValue == null || sessionValue.isBlank()) {
      filterChain.doFilter(request, response);
      return;
    }

    BaggageContextHolder.set(sessionValue);

    Baggage updated =
        Baggage.current().toBuilder()
            .put(properties.getBaggageKey(), sessionValue)
            .build();
    Context newContext = Context.current().with(updated);

    try (Scope scope = newContext.makeCurrent()) {
      filterChain.doFilter(request, response);
    } finally {
      BaggageContextHolder.clear();
    }
  }

  private String resolveSessionValue(HttpServletRequest request) {
    return switch (properties.getRole()) {
      case ORIGINATOR -> {
        String configured = properties.getSessionValue();
        yield (configured != null && !configured.isBlank()) ? configured.trim() : null;
      }
      case FORWARDER, TERMINAL -> {
        String header = request.getHeader(properties.getHeaderName());
        yield (header != null && !header.isBlank()) ? header.trim() : null;
      }
    };
  }
}
