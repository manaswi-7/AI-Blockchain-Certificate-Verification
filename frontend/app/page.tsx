"use client";
import { FormEvent, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api";

export default function Home() {
  const [id,setId]=useState(""); const [result,setResult]=useState<any>(null); const [loading,setLoading]=useState(false);
  async function verify(e:FormEvent){e.preventDefault();setLoading(true);setResult(null);try{const r=await fetch(`${API}/verify/${encodeURIComponent(id)}`);setResult(await r.json())}catch{setResult({result:"ERROR",reason:"Backend is unavailable. Start the Spring Boot API."})}finally{setLoading(false)}}
  return <main className="page"><nav><b>CertiChain</b><span>AI + Blockchain Certificate Verification</span><a href="/login">Issuer Login</a></nav><section className="hero"><div><p className="eyebrow">ISSUE · SECURE · VERIFY</p><h1>Trust every academic certificate.</h1><p className="lead">Issue certificates securely, anchor their cryptographic identity on blockchain, and verify them instantly with a certificate ID or QR reference.</p><form onSubmit={verify} className="verify"><input value={id} onChange={e=>setId(e.target.value)} placeholder="Enter certificate ID" required/><button disabled={loading}>{loading?"Checking…":"Verify certificate"}</button></form>{result&&<div className={`result ${result.result?.toLowerCase()}`}><strong>{result.result}</strong><p>{result.reason || (result.hashMatch?"Registered certificate and hash matched.":"Verification completed.")}</p>{result.certificate&&<small>{result.certificate.recipient_name} · {result.certificate.course} · {result.certificate.institution}</small>}</div>}</div><div className="card"><div className="shield">✓</div><h2>Cryptographic verification</h2><p>Certificate identity is represented by a SHA-256 hash. Blockchain anchoring is designed to make later modification detectable.</p><div className="steps"><span>01 Issue</span><span>02 Hash</span><span>03 Anchor</span><span>04 Verify</span></div></div></section></main>
}
