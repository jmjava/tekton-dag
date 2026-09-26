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
 * Temporary echo helper until this app depends on baggage-spring-boot-starter.
 * Prefer the starter + BaggagePropagator for outgoing calls — do not copy
 * headers by hand in controllers.
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
    String session = value.trim();
    request.setAttribute("dev-session", session);
    Baggage updated = Baggage.current().toBuilder().put(baggageKey, session).build();
    Context newContext = Context.current().with(updated);
    try (Scope scope = newContext.makeCurrent()) {
      filterChain.doFilter(request, response);
    }
  }
}
