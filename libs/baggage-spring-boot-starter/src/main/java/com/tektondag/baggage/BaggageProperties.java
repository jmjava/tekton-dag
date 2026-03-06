package com.tektondag.baggage;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "baggage")
public class BaggageProperties {

  private boolean enabled = false;
  private BaggageRole role = BaggageRole.FORWARDER;
  private String headerName = "x-dev-session";
  private String baggageKey = "dev-session";
  private String sessionValue = "";

  public boolean isEnabled() {
    return enabled;
  }

  public void setEnabled(boolean enabled) {
    this.enabled = enabled;
  }

  public BaggageRole getRole() {
    return role;
  }

  public void setRole(BaggageRole role) {
    this.role = role;
  }

  public String getHeaderName() {
    return headerName;
  }

  public void setHeaderName(String headerName) {
    this.headerName = headerName;
  }

  public String getBaggageKey() {
    return baggageKey;
  }

  public void setBaggageKey(String baggageKey) {
    this.baggageKey = baggageKey;
  }

  public String getSessionValue() {
    return sessionValue;
  }

  public void setSessionValue(String sessionValue) {
    this.sessionValue = sessionValue;
  }
}
