"use client";

import { FormEvent, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api";

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

export default function VerifyPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true); setResult(null); setMessage("Running OCR → AI → SHA-256 → Blockchain verification…");
    try {
      const body = new FormData(); body.append("file", file);
      const response = await fetch(`${API}/verify/upload`, { method: "POST", body });
      const data = await response.json(); setResult(data);
      setMessage(response.ok ? "Verification completed." : data.message || data.error || "Verification failed.");
    } catch { setMessage("Verification service is unavailable. Please try again later."); }
    finally { setLoading(false); }
  }

  return (
    <main className="page">
      <nav><b>CertiChain</b><span>Certificate Verification</span><a href="/">Home</a></nav>
      <section style={{ maxWidth: 850, margin: "50px auto", padding: "0 24px" }}>
        <p className="eyebrow">CERTIFICATE VERIFICATION</p>
        <h1>Upload a certificate to verify it</h1>
        <p className="lead">No certificate ID is required. Upload the certificate image and the system will use OCR to find the ID, AI to assess possible tampering, and blockchain to verify its registered hash.</p>
        <form onSubmit={submit} className="verify" style={{ marginTop: 28, display: "grid", gap: 16 }}>
          <label style={{ display: "grid", gap: 8 }}><strong>Certificate image</strong><input type="file" accept="image/png,image/jpeg,image/jpg" onChange={(e) => { setFile(e.target.files?.[0] || null); setResult(null); }} /></label>
          <button disabled={!file || loading}>{loading ? "Verifying…" : "Verify certificate"}</button>
        </form>
        {file && <p>Selected file: <b>{file.name}</b></p>}
        {message && <p>{message}</p>}
        {result && (
          <div className={`result ${String(result.result || "").toLowerCase()}`} style={{ marginTop: 24 }}>
            <h2>{resultLabel(result.result)}</h2>
            {result.certificateId && <p><b>Certificate ID:</b> {result.certificateId}</p>}
            {result.extractedFields && <p><b>OCR extracted:</b> {JSON.stringify(result.extractedFields)}</p>}
            {result.aiPrediction && <p><b>AI:</b> {result.aiPrediction}{typeof result.aiConfidence === "number" ? ` (${Math.round(result.aiConfidence * 100)}%)` : ""}</p>}
            {typeof result.aiModelAvailable === "boolean" && <p><b>AI model:</b> {result.aiModelAvailable ? "AVAILABLE" : "UNAVAILABLE"}</p>}
            {typeof result.hashMatch === "boolean" && <p><b>SHA-256:</b> {result.hashMatch ? "MATCHED ✓" : "MISMATCH ✗"}</p>}
            {typeof result.blockchainMatch === "boolean" && <p><b>Blockchain:</b> {result.blockchainAvailable === false ? "UNAVAILABLE" : result.blockchainMatch ? "MATCHED ✓" : "NOT MATCHED ✗"}</p>}
            <p>{result.reason}</p>
            {Array.isArray(result.aiIssues) && result.aiIssues.length > 0 && <div><b>AI observations:</b><ul>{result.aiIssues.map((issue: string, i: number) => <li key={i}>{issue}</li>)}</ul></div>}
          </div>
        )}
      </section>
    </main>
  );
}
