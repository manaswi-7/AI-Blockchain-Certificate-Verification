import { NextResponse } from "next/server";
import { createPublicClient, http, keccak256, toBytes } from "viem";
import { polygonAmoy } from "viem/chains";

export const runtime = "nodejs";
export const maxDuration = 60;

const CONTRACT_ABI = [
  {
    type: "function",
    name: "verifyCertificate",
    stateMutability: "view",
    inputs: [
      { name: "certificateIdHash", type: "bytes32" },
      { name: "documentHash", type: "bytes32" },
    ],
    outputs: [{ name: "", type: "bool" }],
  },
] as const;

function sha256Hex(data: ArrayBuffer | string) {
  return crypto.subtle.digest("SHA-256", typeof data === "string" ? new TextEncoder().encode(data) : data)
    .then((hash) => Array.from(new Uint8Array(hash), (b) => b.toString(16).padStart(2, "0")).join(""));
}

export async function GET() {
  return NextResponse.json({
    status: "UP",
    service: "certificate-verification-api",
    mode: "vercel-native",
  });
}

export async function POST(request: Request) {
  try {
    const form = await request.formData();
    const file = form.get("file");
    const suppliedId = String(form.get("certificateId") || "").trim();

    if (!(file instanceof File)) {
      return NextResponse.json({ result: "UNVERIFIED", reason: "Certificate image is required." }, { status: 400 });
    }

    if (file.size === 0) {
      return NextResponse.json({ result: "UNVERIFIED", reason: "The uploaded certificate is empty." }, { status: 400 });
    }

    if (file.size > 10_000_000) {
      return NextResponse.json({ result: "UNVERIFIED", reason: "File must be 10 MB or smaller." }, { status: 413 });
    }

    if (!["image/png", "image/jpeg"].includes(file.type)) {
      return NextResponse.json({ result: "UNVERIFIED", reason: "Please upload a PNG or JPEG certificate image." }, { status: 400 });
    }

    const bytes = await file.arrayBuffer();
    const documentHash = await sha256Hex(bytes);

    if (!suppliedId) {
      return NextResponse.json({
        result: "UNVERIFIED",
        reason: "The Vercel-native verifier needs the Certificate ID to perform the blockchain lookup. Enter the Certificate ID and try again.",
        aiPrediction: "UNAVAILABLE",
        aiModelAvailable: false,
        hash: documentHash,
      });
    }

    const certificateIdHash = await sha256Hex(suppliedId);
    const rpcUrl = process.env.BLOCKCHAIN_RPC_URL;
    const contractAddress = process.env.BLOCKCHAIN_CONTRACT_ADDRESS as `0x${string}` | undefined;

    if (!rpcUrl || !contractAddress) {
      return NextResponse.json({
        result: "UNVERIFIED",
        certificateId: suppliedId,
        hashMatch: false,
        blockchainMatch: false,
        blockchainAvailable: false,
        aiPrediction: "UNAVAILABLE",
        aiModelAvailable: false,
        reason: "Certificate ID was received and the SHA-256 fingerprint was calculated, but blockchain verification is not configured on this Vercel deployment yet. Add BLOCKCHAIN_RPC_URL and BLOCKCHAIN_CONTRACT_ADDRESS in Vercel.",
        documentHash,
      });
    }

    const client = createPublicClient({
      chain: polygonAmoy,
      transport: http(rpcUrl),
    });

    const blockchainMatch = await client.readContract({
      address: contractAddress,
      abi: CONTRACT_ABI,
      functionName: "verifyCertificate",
      args: [`0x${certificateIdHash}` as `0x${string}`, `0x${documentHash}` as `0x${string}`],
    });

    return NextResponse.json({
      result: blockchainMatch ? "VERIFIED_WITHOUT_AI" : "INVALID",
      certificateId: suppliedId,
      hashMatch: blockchainMatch,
      blockchainMatch,
      blockchainAvailable: true,
      aiPrediction: "UNAVAILABLE",
      aiModelAvailable: false,
      reason: blockchainMatch
        ? "The uploaded file's SHA-256 fingerprint matches the certificate record anchored on Polygon Amoy. AI visual analysis is not running in this Vercel-only deployment yet."
        : "The uploaded file does not match the blockchain record for this Certificate ID. The document may have been modified.",
      documentHash,
    });
  } catch (error) {
    console.error("verification error", error);
    return NextResponse.json({
      result: "UNVERIFIED",
      reason: "The Vercel verification API could not complete the check. Verify the blockchain configuration and try again.",
      aiPrediction: "UNAVAILABLE",
      aiModelAvailable: false,
    }, { status: 500 });
  }
}
