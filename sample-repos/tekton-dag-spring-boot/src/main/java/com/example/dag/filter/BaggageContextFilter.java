package com.example.dag.filter;

import io.opentelemetry.api.baggage.Baggage;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.Scope;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Propagates dev-session (or custom header) into OpenTelemetry baggage and context.
 * Uses Baggage.current().toBuilder() for API compatibility with OpenTelemetry 1.44+.
 */
@Component
@Order(1)
public class BaggageContextFilter extends OncePerRequestFilter {

  public static final String DEFAULT_HEADER = "x-dev-session";
  public static final String DEFAULT_BAGGAGE_KEY = "dev-session";

  @Value("${baggage.header-name:" + DEFAULT_HEADER + "}")
  private String headerName;

  @Value("${baggage.key:" + DEFAULT_BAGGAGE_KEY + "}")
  private String baggageKey;

  @Override
  protected void doFilterInternal(
      HttpServletRequest request,
      HttpServletResponse response,
      FilterChain filterChain)
      throws ServletException, IOException {
    String value = request.getHeader(headerName);
    if (value == null || value.isBlank()) {
      filterChain.doFilter(request, response);
      return;
    }
    // Use current().toBuilder() for compatibility (Baggage.builder() not available in all versions)
    Baggage updated =
        Baggage.current().toBuilder().put(baggageKey, value.trim()).build();
    Context newContext = Context.current().with(updated);
    try (Scope scope = newContext.makeCurrent()) {
      filterChain.doFilter(request, response);
    }
  }
}
