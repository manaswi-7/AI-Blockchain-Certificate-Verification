package com.certificate.verification;

import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.client.RestClient;

@Service
public class AiService {
  private final RestClient client;
  public AiService(@Value("${app.ai-url:http://localhost:8000}") String url) { this.client=RestClient.builder().baseUrl(url).build(); }
  public Map<?,?> analyze(byte[] file, String filename) {
    var resource=new ByteArrayResource(file){ @Override public String getFilename(){ return filename; } };
    var body=new LinkedMultiValueMap<String,Object>(); body.add("file",resource);
    return client.post().uri("/analyze").contentType(MediaType.MULTIPART_FORM_DATA).body(body).retrieve().body(Map.class);
  }
}
