import { NextResponse } from "next/server";
import { createPublicClient, http } from "viem";
import { polygonAmoy } from "viem/chains";

export const runtime = "nodejs";

const ABI = [
  {
    type: "function",
    name: "getCertificate",
    stateMutability: "view",
    inputs: [{ name: "certificateId", type: "bytes32" }],
    outputs: [
      { name: "documentHash", type: "bytes32" },
      { name: "timestamp", type: "uint256" },
      { name: "issuer", type: "address" },
      { name: "exists", type: "bool" },
    ],
  },
] as const;

function isAddress(value: string | undefined): value is `0x${string}` {
  return !!value && /^0x[a-fA-F0-9]{40}$/.test(value);
}

async function sha256Hex(value: string) {
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(hash), (b) => b.toString(16).padStart(2, "0")).join("");
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ certificateId: string }> },
) {
  const { certificateId } = await params;
  const rpcUrl = process.env.BLOCKCHAIN_RPC_URL || process.env.POLYGON_AMOY_RPC_URL || "";
  const contractAddress = process.env.BLOCKCHAIN_CONTRACT_ADDRESS;

  if (!rpcUrl || !isAddress(contractAddress)) {
    return NextResponse.json({
      result: "UNVERIFIED",
      certificateId,
      blockchainAvailable: false,
      reason: "Blockchain verification is not configured for this deployment.",
    });
  }

  try {
    const client = createPublicClient({
      chain: polygonAmoy,
      transport: http(rpcUrl),
    });
    const idHash = `0x${await sha256Hex(certificateId)}` as `0x${string}`;
    const record = await client.readContract({
      address: contractAddress,
      abi: ABI,
      functionName: "getCertificate",
      args: [idHash],
    });

    const [documentHash, timestamp, issuer, exists] = record;
    return NextResponse.json({
      result: exists ? "REGISTERED" : "INVALID",
      certificateId,
      documentHash,
      timestamp: timestamp.toString(),
      issuer,
      blockchainMatch: Boolean(exists),
      blockchainAvailable: true,
      reason: exists
        ? "Certificate ID is registered on Polygon Amoy. Upload the exact certificate file to verify its SHA-256 fingerprint."
        : "Certificate ID is not registered on the configured blockchain registry.",
    });
  } catch (error) {
    console.error("certificate lookup error", error);
    return NextResponse.json(
      {
        result: "UNVERIFIED",
        certificateId,
        blockchainAvailable: false,
        reason: "Unable to read the configured blockchain registry.",
      },
      { status: 502 },
    );
  }
}
