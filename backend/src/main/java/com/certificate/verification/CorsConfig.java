package com.certificate.verification;

import java.util.List;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Configuration
public class CorsConfig {
  @Bean
  CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration c=new CorsConfiguration();
    c.setAllowedOrigins(List.of("http://localhost:3000","http://127.0.0.1:3000"));
    c.setAllowedMethods(List.of("GET","POST","PUT","DELETE","OPTIONS"));
    c.setAllowedHeaders(List.of("*"));
    c.setAllowCredentials(true);
    UrlBasedCorsConfigurationSource s=new UrlBasedCorsConfigurationSource();
    s.registerCorsConfiguration("/**",c); return s;
  }
}
