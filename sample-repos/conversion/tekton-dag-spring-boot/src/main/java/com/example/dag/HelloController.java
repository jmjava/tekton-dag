package com.example.dag;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

@RestController
public class HelloController {

  @Value("${APP_NAME:tekton-dag-spring-boot}")
  private String appName;

  @Value("${DOWNSTREAM_URL:}")
  private String downstreamUrl;

  @Autowired(required = false)
  private RestTemplate restTemplate;

  @GetMapping({"/", "/propagation"})
  public Map<String, Object> hello() {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("app", appName);
    body.put("session", currentSession());
    body.put("hops", downstreamHops());
    return body;
  }

  private static String currentSession() {
    try {
      Class<?> holder = Class.forName("com.tektondag.baggage.BaggageContextHolder");
      Object value = holder.getMethod("get").invoke(null);
      return value == null ? null : String.valueOf(value);
    } catch (Exception ignored) {
      return null;
    }
  }

  private List<Object> downstreamHops() {
    List<Object> hops = new ArrayList<>();
    if (downstreamUrl == null || downstreamUrl.isBlank() || restTemplate == null) {
      return hops;
    }
    try {
      String url = downstreamUrl.replaceAll("/$", "") + "/propagation";
      ResponseEntity<Map> resp = restTemplate.getForEntity(url, Map.class);
      if (resp.getBody() != null) {
        hops.add(resp.getBody());
      }
    } catch (Exception exc) {
      hops.add(Map.of("error", String.valueOf(exc.getMessage())));
    }
    return hops;
  }
}
