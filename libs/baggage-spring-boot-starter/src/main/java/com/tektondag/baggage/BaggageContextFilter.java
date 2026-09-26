package com.tektondag.baggage;

import io.opentelemetry.api.baggage.Baggage;
import io.opentelemetry.context.Context;
import io.opentelemetry.context.Scope;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Incoming filter. Stores the original override header in request context so
 * outbound interceptors can copy it hop-to-hop.
 */
public class BaggageContextFilter extends OncePerRequestFilter {

  private final BaggageProperties properties;

  public BaggageContextFilter(BaggageProperties properties) {
    this.properties = properties;
  }

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
      throws ServletException, IOException {

    String sessionValue = resolveSessionValue(request);

    if (sessionValue == null || sessionValue.isBlank()) {
      filterChain.doFilter(request, response);
      return;
    }

    BaggageContextHolder.set(sessionValue);

    Baggage updated =
        Baggage.current().toBuilder().put(properties.getBaggageKey(), sessionValue).build();
    Context newContext = Context.current().with(updated);

    try (Scope scope = newContext.makeCurrent()) {
      filterChain.doFilter(request, response);
    } finally {
      BaggageContextHolder.clear();
    }
  }

  private String resolveSessionValue(HttpServletRequest request) {
    return BaggagePolicy.incomingSession(
        properties.getRole(),
        request.getHeader(properties.getHeaderName()),
        cookieValue(request, properties.getHeaderName()),
        request.getParameter(properties.getHeaderName()),
        properties.getSessionValue());
  }

  static String cookieValue(HttpServletRequest request, String name) {
    Cookie[] cookies = request.getCookies();
    if (cookies == null) {
      return null;
    }
    for (Cookie cookie : cookies) {
      if (name.equalsIgnoreCase(cookie.getName())) {
        return cookie.getValue();
      }
    }
    return null;
  }
}
