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
  const [result, setResult] = useState<Verification | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

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
      const body = new FormData(); body.append("file", file);
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
          <form onSubmit={verify} className="verify" style={{ display: "grid", gap: 14 }}>
            <label style={{ display: "grid", gap: 8 }}><strong>Upload certificate</strong><input type="file" accept="image/png,image/jpeg,image/jpg" onChange={(e) => { setFile(e.target.files?.[0] || null); setResult(null); setMessage(""); }} /></label>
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
