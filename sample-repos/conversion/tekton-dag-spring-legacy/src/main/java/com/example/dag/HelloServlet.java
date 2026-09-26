package com.example.dag;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@WebServlet(urlPatterns = {"/", "/propagation"})
public class HelloServlet extends HttpServlet {
  @Override
  protected void doGet(HttpServletRequest req, HttpServletResponse resp)
      throws ServletException, IOException {
    resp.setContentType("application/json");
    String session = currentSession();
    String app = System.getenv().getOrDefault("APP_NAME", "tekton-dag-spring-legacy");
    String json =
        "{\"app\":\""
            + jsonEscape(app)
            + "\",\"session\":"
            + (session == null ? "null" : "\"" + jsonEscape(session) + "\"")
            + ",\"hops\":[]}";
    resp.getWriter().print(json);
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

  private static String jsonEscape(String raw) {
    return raw.replace("\\", "\\\\").replace("\"", "\\\"");
  }
}
