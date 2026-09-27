package com.example.dag;

import jakarta.servlet.http.HttpServletRequest;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

  @Value("${APP_NAME:tekton-dag-spring-boot-gradle}")
  private String appName;

  @GetMapping({"/", "/propagation"})
  public Map<String, Object> hello(HttpServletRequest request) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("app", appName);
    body.put("session", currentSession(request));
    body.put("hops", List.<Object>of());
    return body;
  }

  private static String currentSession(HttpServletRequest request) {
    Object attr = request.getAttribute("dev-session");
    if (attr != null && !String.valueOf(attr).isBlank()) {
      return String.valueOf(attr);
    }
    try {
      Class<?> holder = Class.forName("com.tektondag.baggage.BaggageContextHolder");
      Object value = holder.getMethod("get").invoke(null);
      return value == null ? null : String.valueOf(value);
    } catch (Exception ignored) {
      return null;
    }
  }
}
