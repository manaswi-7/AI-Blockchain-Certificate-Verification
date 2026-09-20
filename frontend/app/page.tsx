"use client";

import { FormEvent, useState } from "react";

const API = "/api";

type Verification = {
  result?: string;
  reason?: string;
  certificateId?: string;
  aiPrediction?: string;
  aiConfidence?: number;
  aiModelAvailable?: boolean;
  ocrFields?: Record<string, unknown>;
  aiRecommendation?: string;
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
    case "PROCESSED": return "Processed — blockchain not configured";
    default: return result || "Verification result";
  }
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [certificateId, setCertificateId] = useState("");
  const [result, setResult] = useState<Verification | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  function detectCertificateId(filename: string) {
    const match = filename.match(/CERT[0-9]{6,}/i);
    return match ? match[0].toUpperCase() : "";
  }

  async function verify(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true); setResult(null);


    setMessage("Analyzing certificate: OCR → AI → SHA-256 → Blockchain…");
    try {
      const body = new FormData();
      body.append("file", file);
      const detectedId = detectCertificateId(file.name);
      const idToSend = certificateId.trim() || detectedId;
      if (idToSend) body.append("certificateId", idToSend);
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
      <nav><div className="brand"><span className="brand-mark">✓</span><div><b>CertiChain</b><small>Certificate Verification</small></div></div><div className="nav-links"><a href="#verify">Verify</a><a href="/login">Issuer Login</a></div></nav>
      <section className="hero" id="verify">
        <div>
          <div className="hero-badge"><span>●</span> SECURE DOCUMENT VERIFICATION</div>
          <h1>Verify certificates with <span>AI + Blockchain.</span></h1>
          <p className="lead">Upload an academic certificate and let CertiChain check its identity, visual authenticity, cryptographic fingerprint, and blockchain record.</p>
          <form onSubmit={verify} className="verify">
            <label className="upload-box">
              <span className="upload-icon">↑</span>
              <span className="upload-title">{file ? file.name : "Choose a certificate to verify"}</span>
              <span className="upload-subtitle">{file ? "Certificate selected" : "PNG, JPG or JPEG · Max 10 MB"}</span>
              <input type="file" accept="image/png,image/jpeg,image/jpg" onChange={(e) => { const selected = e.target.files?.[0] || null; setFile(selected); setResult(null); setMessage(""); if (selected) { const detected = detectCertificateId(selected.name); if (detected && !certificateId) setCertificateId(detected); } }} />
            </label>
            <div className="id-row">
              <label className="field"><span>Certificate ID <em>Optional</em></span><input value={certificateId} onChange={(e) => setCertificateId(e.target.value)} placeholder="Auto-detected from filename when possible" /></label>
              <button className="verify-button" disabled={!file || loading}>{loading ? "Verifying…" : "Verify certificate →"}</button>
            </div>
          </form>
          {file && <p style={{ marginTop: 12 }}>Selected: <b>{file.name}</b></p>}
          {message && <p>{message}</p>}
          {result && (
            <div className={`result ${result.result?.toLowerCase()}`} style={{ marginTop: 20 }}>
              <strong>{resultLabel(result.result)}</strong>
              {result.certificateId && <p>Certificate ID: <b>{result.certificateId}</b></p>}
              {result.aiPrediction && <p>AI analysis: <b>{result.aiPrediction}</b>{typeof result.aiConfidence === "number" && ` (${Math.round(result.aiConfidence * 100)}%)`}</p>}{result.aiRecommendation && <p>{result.aiRecommendation}</p>}
              <p>SHA-256: <b>{result.documentHash ? "CALCULATED ✓" : "NOT CALCULATED"}</b></p>
              <p>Blockchain: <b>{result.blockchainAvailable === false ? "NOT CHECKED" : result.blockchainMatch ? "MATCHED ✓" : "NOT MATCHED ✗"}</b></p>
              {result.result === "VERIFIED_WITHOUT_AI" && <p><b>Note:</b> AI visual analysis was not available for this verification.</p>}
              <p>{result.reason}</p>
            </div>
          )}
        </div>
        <div className="card"><div className="card-top"><div className="shield">✓</div><span>5-layer check</span></div><h2>Built to detect what matters.</h2><p>Every upload passes through multiple verification layers before a result is shown.</p><div className="steps"><span><b>01</b> OCR extraction</span><span><b>02</b> AI tamper check</span><span><b>03</b> SHA-256 hash</span><span><b>04</b> Blockchain match</span><span><b>05</b> Final decision</span></div></div>
      </section>
    </main>
  );
}
