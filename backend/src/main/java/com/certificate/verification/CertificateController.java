package com.certificate.verification;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDate;
import java.util.HexFormat;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class CertificateController {
  private final JdbcTemplate db;
  public CertificateController(JdbcTemplate db) { this.db=db; }

  @GetMapping("/health") public Map<String,String> health() { return Map.of("status","ok"); }

  @PostMapping("/certificates")
  public Map<String,Object> issue(@RequestBody Map<String,String> b) throws Exception {
    String id=b.get("certificateId"), name=b.get("recipientName"), course=b.get("course"), institution=b.get("institution");
    if (id==null||name==null||course==null||institution==null) throw new IllegalArgumentException("Required certificate fields are missing");
    String canonical=id+"|"+name+"|"+course+"|"+institution+"|"+b.getOrDefault("issueDate",LocalDate.now().toString());
    String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(canonical.getBytes(StandardCharsets.UTF_8)));
    db.update("INSERT INTO certificates(certificate_id,recipient_name,course,institution,issue_date,validity,status,document_hash) VALUES(?,?,?,?,?,?,'ISSUED',?)",id,name,course,institution,b.getOrDefault("issueDate",LocalDate.now().toString()),b.getOrDefault("validity","VALID"),hash);
    return Map.of("certificateId",id,"documentHash",hash,"status","ISSUED");
  }

  @GetMapping("/certificates") public Object list() { return db.queryForList("SELECT certificate_id,recipient_name,course,institution,issue_date,status,document_hash,blockchain_reference FROM certificates ORDER BY created_at DESC"); }

  @GetMapping("/verify/{certificateId}")
  public Map<String,Object> verify(@PathVariable String certificateId, @RequestParam(required=false) String hash) {
    var rows=db.queryForList("SELECT certificate_id,recipient_name,course,institution,issue_date,status,document_hash,blockchain_reference FROM certificates WHERE certificate_id=?",certificateId);
    if (rows.isEmpty()) { db.update("INSERT INTO verification_records(certificate_id,result,reason) VALUES(?,?,'Certificate ID not found')",certificateId,"INVALID"); return Map.of("result","INVALID","reason","Certificate ID not found"); }
    var c=rows.get(0); boolean match=hash==null || hash.equalsIgnoreCase((String)c.get("document_hash"));
    String result=match ? "GENUINE" : "TAMPERED";
    db.update("INSERT INTO verification_records(certificate_id,supplied_hash,result,reason) VALUES(?,?,?,?)",certificateId,hash,result,match?"Database hash matched":"Supplied hash does not match registered hash");
    return Map.of("result",result,"hashMatch",match,"certificate",c);
  }
}
