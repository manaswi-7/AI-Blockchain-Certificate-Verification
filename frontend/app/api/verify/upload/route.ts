import { NextResponse } from "next/server";
import { createPublicClient, http } from "viem";
import { polygonAmoy } from "viem/chains";
import { analyzeCertificate } from "../../../../lib/ai";

export const runtime = "nodejs";
export const maxDuration = 60;

const CONTRACT_ABI = [
  {
    type: "function",
    name: "verifyCertificate",
    stateMutability: "view",
    inputs: [
      { name: "certificateId", type: "bytes32" },
      { name: "documentHash", type: "bytes32" },
    ],
    outputs: [{ name: "", type: "bool" }],
  },
] as const;

function sha256Hex(data: ArrayBuffer | string) {
  return crypto.subtle
    .digest(
      "SHA-256",
      typeof data === "string" ? new TextEncoder().encode(data) : data,
    )
    .then((hash) =>
      Array.from(new Uint8Array(hash), (b) =>
        b.toString(16).padStart(2, "0"),
      ).join(""),
    );
}

function isAddress(value: string | undefined): value is `0x${string}` {
  return !!value && /^0x[a-fA-F0-9]{40}$/.test(value);
}

function getConfig() {
  const rpcUrl =
    process.env.BLOCKCHAIN_RPC_URL ||
    process.env.POLYGON_AMOY_RPC_URL ||
    "";
  const rawContractAddress = process.env.BLOCKCHAIN_CONTRACT_ADDRESS;

  return {
    rpcUrl,
    contractAddress: isAddress(rawContractAddress)
      ? rawContractAddress
      : undefined,
  };
}

export async function GET() {
  const config = getConfig();

  return NextResponse.json({
    status: "UP",
    service: "certificate-verification-api",
    mode: "vercel-native",
    blockchain: {
      network: "Polygon Amoy",
      chainId: 80002,
      configured: Boolean(config.rpcUrl && config.contractAddress),
    },
    ai: {
      available: true,
      mode: "native-vercel-onnx",
      model: "MobileNetV2 certificate tampering classifier",
    },
  });
}

export async function POST(request: Request) {
  try {
    const form = await request.formData();
    const file = form.get("file");
    const suppliedId = String(form.get("certificateId") || "").trim();
    const filename = file instanceof File ? file.name : "";
    const filenameId =
      filename.match(/CERT\d{6,}/i)?.[0]?.toUpperCase() || "";
    const certificateId = suppliedId || filenameId;

    if (!(file instanceof File)) {
      return NextResponse.json(
        { result: "UNVERIFIED", reason: "Certificate image is required." },
        { status: 400 },
      );
    }

    if (file.size === 0) {
      return NextResponse.json(
        { result: "UNVERIFIED", reason: "The uploaded certificate is empty." },
        { status: 400 },
      );
    }

    if (file.size > 10_000_000) {
      return NextResponse.json(
        { result: "UNVERIFIED", reason: "File must be 10 MB or smaller." },
        { status: 413 },
      );
    }

    if (!["image/png", "image/jpeg"].includes(file.type)) {
      return NextResponse.json(
        {
          result: "UNVERIFIED",
          reason: "Please upload a PNG or JPEG certificate image.",
        },
        { status: 400 },
      );
    }

    const bytes = await file.arrayBuffer();
    const documentHash = await sha256Hex(bytes);

    let aiPrediction = "UNAVAILABLE";
    let aiConfidence: number | undefined;
    let aiModelAvailable = false;
    let ocrFields: Record<string, unknown> | undefined;
    let aiRecommendation: string | undefined;

    try {
      const aiData = await analyzeCertificate(bytes);
      aiPrediction = aiData.classification;
      aiConfidence = aiData.confidence;
      aiModelAvailable = aiData.model_available;
      aiRecommendation = aiData.recommendation;
    } catch (aiError) {
      console.error("Native AI inference unavailable", aiError);
    }

    if (!certificateId) {
      return NextResponse.json({
        result: "UNVERIFIED",
        reason:
          "Certificate ID is required for blockchain verification. Enter the Certificate ID or use a filename such as CERT2025000003.png.",
        aiPrediction,
        aiConfidence,
        aiModelAvailable,
        ocrFields,
        aiRecommendation,
        documentHash,
        blockchainAvailable: false,
      });
    }

    const config = getConfig();

    if (!config.rpcUrl || !config.contractAddress) {
      return NextResponse.json({
        result: "UNVERIFIED",
        certificateId,
        aiPrediction,
        aiConfidence,
        aiModelAvailable,
        ocrFields,
        aiRecommendation,
        documentHash,
        blockchainMatch: undefined,
        blockchainAvailable: false,
        reason:
          "Blockchain verification is not configured yet. Deploy CertificateRegistry to Polygon Amoy, then set BLOCKCHAIN_RPC_URL and BLOCKCHAIN_CONTRACT_ADDRESS in Vercel and redeploy.",
      });
    }

    const certificateIdHash = await sha256Hex(certificateId);

    const client = createPublicClient({
      chain: polygonAmoy,
      transport: http(config.rpcUrl),
    });

    const blockchainMatch = await client.readContract({
      address: config.contractAddress,
      abi: CONTRACT_ABI,
      functionName: "verifyCertificate",
      args: [
        `0x${certificateIdHash}` as `0x${string}`,
        `0x${documentHash}` as `0x${string}`,
      ],
    });

    return NextResponse.json({
      result: blockchainMatch ? "VERIFIED" : "INVALID",
      certificateId,
      hashMatch: blockchainMatch,
      blockchainMatch,
      blockchainAvailable: true,
      aiPrediction,
      aiConfidence,
      aiModelAvailable,
      ocrFields,
      aiRecommendation,
      documentHash,
      reason: blockchainMatch
        ? "The uploaded file matches the certificate record anchored on Polygon Amoy."
        : "The uploaded file does not match the blockchain record for this Certificate ID. Use the exact original file that was anchored.",
    });
  } catch (error) {
    console.error("verification error", error);

    return NextResponse.json(
      {
        result: "UNVERIFIED",
        reason:
          "Blockchain verification failed. Check the Polygon Amoy RPC URL and deployed CertificateRegistry address in Vercel.",
        blockchainAvailable: false,
      },
      { status: 502 },
    );
  }
}
