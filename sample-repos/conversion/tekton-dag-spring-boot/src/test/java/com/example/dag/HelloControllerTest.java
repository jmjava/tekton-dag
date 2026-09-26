package com.example.dag;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
class HelloControllerTest {

  @Autowired private MockMvc mockMvc;

  @Test
  void rootEndpointReturnsHopReport() throws Exception {
    mockMvc
        .perform(get("/"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.app").value("tekton-dag-spring-boot"))
        .andExpect(jsonPath("$.hops").isArray());
  }

  @Test
  void propagationEndpointExists() throws Exception {
    mockMvc.perform(get("/propagation")).andExpect(status().isOk());
  }
}
