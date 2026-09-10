package com.certificate.verification;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api")
public class CertificateController {
  private final JdbcTemplate db;
  private final QrService qr;
  private final BlockchainService blockchain;
  private final AiService ai;

  public CertificateController(JdbcTemplate db, QrService qr, BlockchainService blockchain, AiService ai) {
    this.db = db;
    this.qr = qr;
    this.blockchain = blockchain;
    this.ai = ai;
  }

  @GetMapping("/health")
  public Map<String, String> health() { return Map.of("status", "ok"); }

  @PostMapping(value = "/certificates", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
  public Map<String, Object> issue(
      @RequestParam String certificateId,
      @RequestParam String recipientName,
      @RequestParam String course,
      @RequestParam String institution,
      @RequestParam(required = false) String issueDate,
      @RequestParam(required = false, defaultValue = "VALID") String validity,
      @RequestPart MultipartFile file) throws Exception {
    validateImage(file);
    String date = issueDate == null || issueDate.isBlank() ? LocalDate.now().toString() : issueDate;
    if (!db.queryForList("SELECT 1 FROM certificates WHERE certificate_id=?", certificateId).isEmpty()) {
      throw new IllegalArgumentException("Certificate ID already exists");
    }
    String documentHash = sha256(file.getBytes());
    String certificateKey = sha256(certificateId);
    String verificationUrl = System.getenv().getOrDefault("VERIFICATION_URL", "http://localhost:3000/verify") + "/" + certificateId;
    String qrCode = qr.generateDataUrl(verificationUrl);
    String txHash = blockchain.anchor(certificateKey, documentHash);
    db.update("INSERT INTO certificates(certificate_id,recipient_name,course,institution,issue_date,validity,status,document_hash,blockchain_reference,qr_code) VALUES(?,?,?,?,?,?,'ISSUED',?,?,?)",
        certificateId, recipientName, course, institution, date, validity, documentHash, txHash, qrCode);
    db.update("INSERT INTO blockchain_transactions(certificate_id,transaction_hash,network,status) VALUES(?,?,?,?)",
        certificateId, txHash, "Polygon Amoy", "CONFIRMED");
    return Map.of("certificateId", certificateId, "documentHash", documentHash, "blockchainTransaction", txHash, "qrCode", qrCode, "status", "ISSUED");
  }

  @GetMapping("/certificates")
  public Object list() {
    return db.queryForList("SELECT certificate_id,recipient_name,course,institution,issue_date,status,document_hash,blockchain_reference,qr_code FROM certificates ORDER BY created_at DESC");
  }

  @GetMapping("/verify/{certificateId}")
  public Map<String, Object> verify(@PathVariable String certificateId, @RequestParam(required = false) String hash) {
    return verifyRegisteredCertificate(certificateId, hash, null);
  }

  @PostMapping(value = "/verify/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
  public Map<String, Object> verifyUpload(@RequestPart MultipartFile file) throws Exception {
    validateImage(file);
    Map<?, ?> aiResult;
    try {
      aiResult = ai.analyze(file.getBytes(), file.getOriginalFilename() == null ? "certificate" : file.getOriginalFilename());
    } catch (Exception e) {
      Map<String, Object> response = new HashMap<>();
      response.put("result", "UNVERIFIED");
      response.put("reason", "AI/OCR service is unavailable. The certificate cannot be fully verified right now.");
      response.put("aiPrediction", "UNAVAILABLE");
      response.put("aiServiceAvailable", false);
      return response;
    }

    Object extracted = aiResult.get("extracted_fields");
    String certificateId = null;
    if (extracted instanceof Map<?, ?> fields && fields.get("certificate_id") != null) {
      certificateId = String.valueOf(fields.get("certificate_id")).trim();
    }
    if (certificateId == null || certificateId.isBlank()) {
      Map<String, Object> response = new HashMap<>();
      response.put("result", "UNVERIFIED");
      response.put("reason", "OCR could not identify a certificate ID. Please upload a clear certificate image.");
      return withAi(response, aiResult);
    }
    return verifyRegisteredCertificate(certificateId, sha256(file.getBytes()), aiResult);
  }

  private Map<String, Object> verifyRegisteredCertificate(String certificateId, String hash, Map<?, ?> aiResult) {
    var rows = db.queryForList("SELECT certificate_id,recipient_name,course,institution,issue_date,status,document_hash,blockchain_reference,qr_code FROM certificates WHERE certificate_id=?", certificateId);
    if (rows.isEmpty()) {
      recordVerification(certificateId, hash, "INVALID", "Certificate ID not found");
      Map<String, Object> response = new HashMap<>();
      response.put("result", "INVALID");
      response.put("certificateId", certificateId);
      response.put("reason", "Certificate ID was extracted, but it is not registered in the system.");
      return withAi(response, aiResult);
    }

    var certificate = rows.get(0);
    boolean hashMatch = hash == null || hash.equalsIgnoreCase(String.valueOf(certificate.get("document_hash")));
    boolean blockchainMatch = false;
    boolean blockchainAvailable = false;
    String blockchainReason;
    try {
      blockchainMatch = blockchain.verify(sha256(certificateId), String.valueOf(certificate.get("document_hash")));
      blockchainAvailable = true;
      blockchainReason = blockchainMatch ? "Blockchain hash matched" : "Blockchain hash did not match";
    } catch (Exception e) {
      blockchainReason = "Blockchain unavailable or not configured";
    }

    String aiPrediction = aiResult == null ? "NOT_RUN" : String.valueOf(valueOrDefault(aiResult, "classification", "UNAVAILABLE"));
    boolean aiAvailable = aiResult != null && !"UNAVAILABLE".equalsIgnoreCase(aiPrediction);
    String result;
    String reason;

    if (!hashMatch) {
      result = "INVALID";
      reason = "Uploaded certificate hash does not match the registered certificate. Possible tampering detected.";
    } else if (!blockchainAvailable) {
      result = "UNVERIFIED";
      reason = "The local certificate hash matched, but blockchain verification is unavailable. Verification cannot be completed yet.";
    } else if (!blockchainMatch) {
      result = "INVALID";
      reason = "The registered certificate does not match its blockchain record.";
    } else if ("TAMPERED".equalsIgnoreCase(aiPrediction) || "SUSPICIOUS".equalsIgnoreCase(aiPrediction)) {
      result = "WARNING";
      reason = "Blockchain integrity matched, but AI detected possible visual tampering. Manual review is recommended.";
    } else if (!aiAvailable) {
      result = "VERIFIED_WITHOUT_AI";
      reason = "SHA-256 and blockchain verification passed. AI analysis is unavailable, so visual tampering assessment was not performed.";
    } else {
      result = "VERIFIED";
      reason = "AI assessment, SHA-256 fingerprint, and blockchain record passed verification.";
    }

    recordVerification(certificateId, hash, result, reason + "; " + blockchainReason);
    Map<String, Object> response = new HashMap<>();
    response.put("result", result);
    response.put("certificateId", certificateId);
    response.put("hashMatch", hashMatch);
    response.put("blockchainMatch", blockchainMatch);
    response.put("blockchainAvailable", blockchainAvailable);
    response.put("reason", reason);
    response.put("certificate", certificate);
    return withAi(response, aiResult);
  }

  private Object valueOrDefault(Map<?, ?> map, String key, Object fallback) {
    Object value = map.get(key);
    return value == null ? fallback : value;
  }

  private Map<String, Object> withAi(Map<String, Object> response, Map<?, ?> aiResult) {
    if (aiResult != null) {
      response.put("aiPrediction", aiResult.get("classification"));
      response.put("aiConfidence", aiResult.get("confidence"));
      response.put("aiModelAvailable", aiResult.get("model_available"));
      response.put("extractedFields", aiResult.get("extracted_fields"));
      response.put("aiIssues", aiResult.get("issues"));
      response.put("aiRecommendation", aiResult.get("recommendation"));
    }
    return response;
  }

  private void recordVerification(String certificateId, String hash, String result, String reason) {
    db.update("INSERT INTO verification_records(certificate_id,supplied_hash,result,reason) VALUES(?,?,?,?)", certificateId, hash, result, reason);
  }

  private void validateImage(MultipartFile file) {
    if (file.isEmpty()) throw new IllegalArgumentException("Certificate image is required");
    if (file.getSize() > 10_000_000) throw new IllegalArgumentException("File must be 10 MB or smaller");
    String type = file.getContentType();
    if (!("image/png".equals(type) || "image/jpeg".equals(type))) throw new IllegalArgumentException("Please upload a PNG or JPEG certificate image");
  }

  private String sha256(String text) {
    return sha256(text.getBytes(StandardCharsets.UTF_8));
  }

  private String sha256(byte[] data) {
    try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data)); }
    catch (Exception e) { throw new RuntimeException("Unable to calculate SHA-256 hash", e); }
  }
}
