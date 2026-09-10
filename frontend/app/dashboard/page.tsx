"use client";

import { FormEvent, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api";

export default function Dashboard() {
  const [rows, setRows] = useState<any[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState({
    certificateId: "",
    recipientName: "",
    course: "",
    institution: "",
    issueDate: new Date().toISOString().slice(0, 10),
    validity: "VALID",
  });
  const [msg, setMsg] = useState("");

  async function load() {
    const token = localStorage.getItem("token");
    if (!token) return;
    const r = await fetch(`${API}/certificates`, { headers: { Authorization: `Bearer ${token}` } });
    if (r.ok) setRows(await r.json());
  }

  useEffect(() => { load(); }, []);

  async function issue(e: FormEvent) {
    e.preventDefault();
    if (!file) {
      setMsg("Please select the genuine certificate image to register.");
      return;
    }
    setMsg("Registering: SHA-256 → blockchain → QR…");
    try {
      const token = localStorage.getItem("token");
      const body = new FormData();
      Object.entries(form).forEach(([k, v]) => body.append(k, v));
      body.append("file", file);
      const r = await fetch(`${API}/certificates`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body,
      });
      const d = await r.json();
      if (!r.ok) throw Error(d.message || d.error || "Could not register certificate");
      setMsg(`Certificate ${d.certificateId} registered. Blockchain transaction: ${d.blockchainTransaction}`);
      setForm({ ...form, certificateId: "", recipientName: "", course: "" });
      setFile(null);
      load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Request failed");
    }
  }

  return (
    <main className="page">
      <nav>
        <b>CertiChain</b>
        <span>Issuer Dashboard</span>
        <button onClick={() => { localStorage.clear(); location.href = "/login"; }}>Sign out</button>
      </nav>

      <section style={{ maxWidth: 1120, margin: "40px auto", padding: "0 24px" }}>
        <p className="eyebrow">ISSUER · REGISTER · SECURE</p>
        <h1>Register a genuine certificate</h1>
        <p>
          Enter the certificate details and upload the final genuine certificate image.
          The file receives a SHA-256 fingerprint and is registered on the blockchain so later edits can be detected.
        </p>

        <form onSubmit={issue} className="verify" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 24 }}>
          {Object.entries(form).map(([k, v]) => (
            <input key={k} placeholder={k} value={v} onChange={e => setForm({ ...form, [k]: e.target.value })} required />
          ))}
          <label style={{ display: "grid", gap: 6 }}>
            <strong>Genuine certificate image</strong>
            <input type="file" accept="image/png,image/jpeg,image/jpg" onChange={e => setFile(e.target.files?.[0] || null)} required />
          </label>
          <button>Register certificate</button>
        </form>
        <p>{msg}</p>

        <h2 style={{ marginTop: 45 }}>Registered certificates</h2>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", background: "white", borderCollapse: "collapse" }}>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  {[r.certificate_id, r.recipient_name, r.course, r.institution, r.status].map((x, j) => (
                    <td key={j} style={{ padding: 14, borderBottom: "1px solid #eee" }}>{x}</td>
                  ))}
                  <td><a href={`/verify/${r.certificate_id}`}>Open verification</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
