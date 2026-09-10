package com.certificate.verification;

import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
  private final JdbcTemplate db; private final PasswordEncoder encoder; private final JwtService jwt;
  public AuthController(JdbcTemplate db, PasswordEncoder encoder, JwtService jwt) { this.db=db; this.encoder=encoder; this.jwt=jwt; }

  @PostMapping("/register")
  public ResponseEntity<?> register(@RequestBody Map<String,String> b) {
    String name=b.get("fullName"), email=b.get("email"), password=b.get("password");
    if (name==null || email==null || password==null || password.length()<8) return ResponseEntity.badRequest().body(Map.of("error","Name, email and an 8+ character password are required"));
    try { db.update("INSERT INTO users(full_name,email,password_hash,role) VALUES(?,?,?,'VERIFIER')", name,email,encoder.encode(password)); return ResponseEntity.ok(Map.of("message","Account created")); }
    catch (Exception e) { return ResponseEntity.badRequest().body(Map.of("error","Email is already registered")); }
  }

  @PostMapping("/login")
  public ResponseEntity<?> login(@RequestBody Map<String,String> b) {
    try {
      var row=db.queryForMap("SELECT email,password_hash,role,full_name FROM users WHERE email=?", b.get("email"));
      if (!encoder.matches(b.getOrDefault("password",""), (String)row.get("password_hash"))) return ResponseEntity.status(401).body(Map.of("error","Invalid credentials"));
      return ResponseEntity.ok(Map.of("token",jwt.create((String)row.get("email"),(String)row.get("role")),"role",row.get("role"),"fullName",row.get("full_name")));
    } catch(Exception e) { return ResponseEntity.status(401).body(Map.of("error","Invalid credentials")); }
  }
}
