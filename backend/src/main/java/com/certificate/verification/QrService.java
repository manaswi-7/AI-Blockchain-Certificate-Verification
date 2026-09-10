package com.certificate.verification;

import com.google.zxing.BarcodeFormat;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import java.io.ByteArrayOutputStream;
import java.util.Base64;
import org.springframework.stereotype.Service;

@Service
public class QrService {
  public String generateDataUrl(String text) throws Exception {
    BitMatrix matrix = new QRCodeWriter().encode(text, BarcodeFormat.QR_CODE, 320, 320);
    ByteArrayOutputStream out = new ByteArrayOutputStream();
    MatrixToImageWriter.writeToStream(matrix, "PNG", out);
    return "data:image/png;base64," + Base64.getEncoder().encodeToString(out.toByteArray());
  }
}
