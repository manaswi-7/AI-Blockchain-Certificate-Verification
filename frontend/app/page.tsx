"use client";

import { FormEvent, useState } from "react";

const configuredApi = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "");
const API = configuredApi || (process.env.NODE_ENV === "development" ? "http://localhost:8080/api" : "");

type Verification = {
  result?: string;
  reason?: string;
  certificateId?: string;
  aiPrediction?: string;
  aiConfidence?: number;
  aiModelAvailable?: boolean;
  blockchainMatch?: boolean;
  blockchainAvailable?: boolean;
  hashMatch?: boolean;
};

function resultLabel(result?: string) {
  switch (result) {
    case "VERIFIED": return "Verified";
    case "VERIFIED_WITHOUT_AI": return "Verified (AI unavailable)";
    case "WARNING": return "Warning — manual review recommended";
    case "INVALID": return "Invalid";
    case "UNVERIFIED": return "Unverified";
    default: return result || "Verification result";
  }
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [certificateId, setCertificateId] = useState("");
  const [result, setResult] = useState<Verification | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  function downloadDemoCertificate(tampered = false) {
    const canvas = document.createElement("canvas");
    canvas.width = 1000;
    canvas.height = 700;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#f8f6ee";
    ctx.fillRect(0, 0, 1000, 700);
    ctx.strokeStyle = "#23374b";
    ctx.lineWidth = 6;
    ctx.strokeRect(25, 25, 950, 650);
    ctx.fillStyle = "#1e1e1e";
    ctx.textAlign = "center";
    ctx.font = "bold 32px Arial";
    ctx.fillText("GNITS Certificate Verification Demo", 500, 90);
    ctx.font = "bold 42px Arial";
    ctx.fillText("CERTIFICATE OF ACHIEVEMENT", 500, 150);
    ctx.font = "22px Arial";
    ctx.fillText("This is to certify that", 500, 225);
    ctx.font = "bold 38px Arial";
    ctx.fillText("Hasini Kandula", 500, 275);
    ctx.font = "22px Arial";
    ctx.fillText("has successfully completed", 500, 340);
    ctx.font = "bold 30px Arial";
    ctx.fillText("Artificial Intelligence", 500, 390);
    ctx.font = "22px Arial";
    ctx.fillText("Grade: A+", 500, 440);
    ctx.fillText("Certificate ID: CERT-2026-000001", 500, 490);
    ctx.fillText("Issue Date: 01-01-2026", 500, 535);
    if (tampered) {
      ctx.fillStyle = "#f8f6ee";
      ctx.fillRect(250, 245, 500, 50);
      ctx.fillStyle = "#aa1e1e";
      ctx.font = "bold 24px Arial";
      ctx.fillText("MODIFIED RECIPIENT", 500, 278);
    }
    const link = document.createElement("a");
    link.download = tampered ? "test-certificate-tampered.png" : "test-certificate-genuine.png";
    link.href = canvas.toDataURL("image/png");
    link.click();
  }

  async function verify(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true); setResult(null);

    if (!API) {
      setMessage("Verification backend is not configured for this deployment.");
      setLoading(false);
      return;
    }

    setMessage("Analyzing certificate: OCR → AI → SHA-256 → Blockchain…");
    try {
      const body = new FormData();
      body.append("file", file);
      if (certificateId.trim()) body.append("certificateId", certificateId.trim());
      const response = await fetch(`${API}/verify/upload`, { method: "POST", body });
      const data = await response.json().catch(() => ({}));
      setResult(data);
      setMessage(response.ok ? "Verification completed." : data.message || data.error || "Verification failed.");
    } catch {
      setMessage("Backend is unavailable. Please try again when the verification service is running.");
    } finally { setLoading(false); }
  }

  return (
    <main className="page">
      <nav><b>CertiChain</b><span>AI + Blockchain Certificate Verification</span><div style={{ display: "flex", gap: 18, alignItems: "center" }}><a href="/verify">Verify</a><a href="/login">Issuer Login</a></div></nav>
      <section className="hero">
        <div>
          <p className="eyebrow">UPLOAD · ANALYZE · VERIFY</p>
          <h1>Verify a certificate using AI + Blockchain.</h1>
          <p className="lead">Upload the certificate image. The system extracts certificate information with OCR, checks for suspicious visual changes using AI, generates a SHA-256 fingerprint, and compares it with the immutable blockchain record.</p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 6 }}>
            <button type="button" onClick={() => downloadDemoCertificate(false)}>Download genuine test certificate</button>
            <button type="button" onClick={() => downloadDemoCertificate(true)}>Download tampered test certificate</button>
          </div>
          <form onSubmit={verify} className="verify" style={{ display: "grid", gap: 14 }}>
            <label style={{ display: "grid", gap: 8 }}><strong>Upload certificate</strong><input type="file" accept="image/png,image/jpeg,image/jpg" onChange={(e) => { setFile(e.target.files?.[0] || null); setResult(null); setMessage(""); }} /></label>
            <label style={{ display: "grid", gap: 8 }}><strong>Certificate ID <span style={{ fontWeight: 400 }}>(optional)</span></strong><input value={certificateId} onChange={(e) => setCertificateId(e.target.value)} placeholder="Enter ID if OCR cannot read it" /></label>
            <button disabled={!file || loading}>{loading ? "Verifying…" : "Verify certificate"}</button>
          </form>
          {file && <p style={{ marginTop: 12 }}>Selected: <b>{file.name}</b></p>}
          {message && <p>{message}</p>}
          {result && (
            <div className={`result ${result.result?.toLowerCase()}`} style={{ marginTop: 20 }}>
              <strong>{resultLabel(result.result)}</strong>
              {result.certificateId && <p>Certificate ID: <b>{result.certificateId}</b></p>}
              {result.aiPrediction && <p>AI analysis: <b>{result.aiPrediction}</b>{typeof result.aiConfidence === "number" && ` (${Math.round(result.aiConfidence * 100)}%)`}</p>}
              {typeof result.hashMatch === "boolean" && <p>SHA-256: <b>{result.hashMatch ? "MATCHED ✓" : "MISMATCH ✗"}</b></p>}
              {typeof result.blockchainMatch === "boolean" && <p>Blockchain: <b>{result.blockchainAvailable === false ? "UNAVAILABLE" : result.blockchainMatch ? "MATCHED ✓" : "NOT MATCHED ✗"}</b></p>}
              {result.result === "VERIFIED_WITHOUT_AI" && <p><b>Note:</b> AI visual analysis was not available for this verification.</p>}
              <p>{result.reason}</p>
            </div>
          )}
        </div>
        <div className="card"><div className="shield">✓</div><h2>How verification works</h2><div className="steps" style={{ display: "grid", gap: 12 }}><span>01 · Upload certificate</span><span>02 · OCR extracts certificate ID</span><span>03 · AI checks visual authenticity</span><span>04 · SHA-256 fingerprint is generated</span><span>05 · Blockchain record is checked</span><span>06 · Final verification decision</span></div></div>
      </section>
    </main>
  );
}
