package com.tektondag.baggage;

import java.io.IOException;
import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;

/**
 * Role-aware baggage filter for Servlet-based (non-Boot) apps.
 * Configured via init-params in web.xml or programmatic registration.
 *
 * Production safety: no-op unless BAGGAGE_ENABLED=true env var is set.
 */
public class BaggageServletFilter implements Filter {

  private BaggageRole role = BaggageRole.FORWARDER;
  private String headerName = "x-dev-session";
  private String baggageKey = "dev-session";
  private String sessionValue = "";
  private Boolean enabledOverride; // null = read from env; non-null = use this value

  @Override
  public void init(FilterConfig config) throws ServletException {
    String r = config.getInitParameter("role");
    if (r != null) role = BaggageRole.fromString(r);
    String h = config.getInitParameter("headerName");
    if (h != null) headerName = h;
    String k = config.getInitParameter("baggageKey");
    if (k != null) baggageKey = k;
    String s = config.getInitParameter("sessionValue");
    if (s != null) sessionValue = s;
  }

  @Override
  public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
      throws IOException, ServletException {

    if (!isEnabled()) {
      chain.doFilter(request, response);
      return;
    }

    String value = resolveValue((HttpServletRequest) request);
    if (value == null || value.isBlank()) {
      chain.doFilter(request, response);
      return;
    }

    BaggageContextHolder.set(value);
    try {
      chain.doFilter(request, response);
    } finally {
      BaggageContextHolder.clear();
    }
  }

  @Override
  public void destroy() {}

  // --- package-private for testing ---

  BaggageRole getRole() {
    return role;
  }

  String getHeaderName() {
    return headerName;
  }

  void setRole(BaggageRole role) {
    this.role = role;
  }

  void setSessionValue(String sessionValue) {
    this.sessionValue = sessionValue;
  }

  void setEnabledOverride(Boolean enabled) {
    this.enabledOverride = enabled;
  }

  private boolean isEnabled() {
    if (enabledOverride != null) return enabledOverride;
    return "true".equalsIgnoreCase(System.getenv("BAGGAGE_ENABLED"));
  }

  private String resolveValue(HttpServletRequest request) {
    return switch (role) {
      case ORIGINATOR -> nonBlank(sessionValue);
      case FORWARDER, TERMINAL -> nonBlank(request.getHeader(headerName));
    };
  }

  private static String nonBlank(String s) {
    return (s != null && !s.isBlank()) ? s.trim() : null;
  }
}
