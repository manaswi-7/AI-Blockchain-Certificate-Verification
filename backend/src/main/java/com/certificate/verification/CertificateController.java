package com.certificate.verification;

import java.security.MessageDigest;
import java.time.LocalDate;
import java.util.HexFormat;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api")
public class CertificateController {
  private final JdbcTemplate db; private final QrService qr; private final BlockchainService blockchain; private final AiService ai;
  public CertificateController(JdbcTemplate db,QrService qr,BlockchainService blockchain,AiService ai){this.db=db;this.qr=qr;this.blockchain=blockchain;this.ai=ai;}
  @GetMapping("/health") public Map<String,String> health(){return Map.of("status","ok");}

  @PostMapping(value="/certificates",consumes=MediaType.MULTIPART_FORM_DATA_VALUE)
  public Map<String,Object> issue(@RequestParam String certificateId,@RequestParam String recipientName,@RequestParam String course,@RequestParam String institution,@RequestParam(required=false) String issueDate,@RequestParam(required=false,defaultValue="VALID") String validity,@RequestPart MultipartFile file)throws Exception{
    if(file.isEmpty())throw new IllegalArgumentException("Certificate file is required");
    if(file.getSize()>10_000_000)throw new IllegalArgumentException("File must be 10 MB or smaller");
    String type=file.getContentType(); if(!("application/pdf".equals(type)||"image/png".equals(type)||"image/jpeg".equals(type)))throw new IllegalArgumentException("Only PDF, PNG and JPEG certificates are supported");
    String date=issueDate==null||issueDate.isBlank()?LocalDate.now().toString():issueDate;
    if(!db.queryForList("SELECT 1 FROM certificates WHERE certificate_id=?",certificateId).isEmpty())throw new IllegalArgumentException("Certificate ID already exists");
    String documentHash=sha256(file.getBytes()); String certificateKey=sha256(certificateId);
    String verificationUrl=System.getenv().getOrDefault("VERIFICATION_URL","http://localhost:3000/verify")+"/"+certificateId;
    String qrCode=qr.generateDataUrl(verificationUrl); String txHash=blockchain.anchor(certificateKey,documentHash);
    db.update("INSERT INTO certificates(certificate_id,recipient_name,course,institution,issue_date,validity,status,document_hash,blockchain_reference,qr_code) VALUES(?,?,?,?,?,?,'ISSUED',?,?,?)",certificateId,recipientName,course,institution,date,validity,documentHash,txHash,qrCode);
    db.update("INSERT INTO blockchain_transactions(certificate_id,transaction_hash,network,status) VALUES(?,?,?,?)",certificateId,txHash,"Polygon Amoy","CONFIRMED");
    try{ai.analyze(file.getBytes(),file.getOriginalFilename()==null?"certificate":file.getOriginalFilename());}catch(Exception ignored){}
    return Map.of("certificateId",certificateId,"documentHash",documentHash,"blockchainTransaction",txHash,"qrCode",qrCode,"status","ISSUED");
  }
  @GetMapping("/certificates") public Object list(){return db.queryForList("SELECT certificate_id,recipient_name,course,institution,issue_date,status,document_hash,blockchain_reference,qr_code FROM certificates ORDER BY created_at DESC");}
  @GetMapping("/verify/{certificateId}") public Map<String,Object> verify(@PathVariable String certificateId,@RequestParam(required=false) String hash){
    var rows=db.queryForList("SELECT certificate_id,recipient_name,course,institution,issue_date,status,document_hash,blockchain_reference,qr_code FROM certificates WHERE certificate_id=?",certificateId);
    if(rows.isEmpty()){db.update("INSERT INTO verification_records(certificate_id,result,reason) VALUES(?,?,'Certificate ID not found')",certificateId,"INVALID");return Map.of("result","INVALID","reason","Certificate ID not found");}
    var c=rows.get(0);boolean dbMatch=hash==null||hash.equalsIgnoreCase((String)c.get("document_hash"));boolean chainMatch=false;String chainReason="Blockchain verification not completed";
    try{chainMatch=blockchain.verify(sha256(certificateId),String.valueOf(c.get("document_hash")));chainReason=chainMatch?"Blockchain hash matched":"Blockchain hash did not match";}catch(Exception e){chainReason="Blockchain unavailable or not configured";}
    String result=dbMatch&&chainMatch?"GENUINE":(hash!=null&&!dbMatch?"TAMPERED":"INVALID");String reason=dbMatch&&chainMatch?"Database and blockchain hashes matched":(!dbMatch?"Supplied document hash does not match":"Certificate could not be verified on blockchain");
    db.update("INSERT INTO verification_records(certificate_id,supplied_hash,result,reason) VALUES(?,?,?,?)",certificateId,hash,result,reason+"; "+chainReason);
    return Map.of("result",result,"hashMatch",dbMatch,"blockchainMatch",chainMatch,"reason",reason,"certificate",c);
  }
  @PostMapping(value="/verify/upload",consumes=MediaType.MULTIPART_FORM_DATA_VALUE) public Map<String,Object> verifyUpload(@RequestParam String certificateId,@RequestPart MultipartFile file)throws Exception{if(file.isEmpty())throw new IllegalArgumentException("Certificate file is required");return verify(certificateId,sha256(file.getBytes()));}
  private String sha256(byte[] data)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));}
}
