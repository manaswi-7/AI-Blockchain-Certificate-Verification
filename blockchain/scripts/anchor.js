const hre = require("hardhat");
const fs = require("fs");
const crypto = require("crypto");

async function main() {
  const certificateId = process.env.CERTIFICATE_ID;
  const filePath = process.env.CERTIFICATE_FILE;
  const contractAddress = process.env.BLOCKCHAIN_CONTRACT_ADDRESS;

  if (!certificateId || !filePath || !contractAddress) {
    throw new Error(
      "Set CERTIFICATE_ID, CERTIFICATE_FILE and BLOCKCHAIN_CONTRACT_ADDRESS before running this script.",
    );
  }

  if (!fs.existsSync(filePath)) {
    throw new Error(`Certificate file not found: ${filePath}`);
  }

  const documentHash = "0x" + crypto
    .createHash("sha256")
    .update(fs.readFileSync(filePath))
    .digest("hex");

  const certificateIdHash = "0x" + crypto
    .createHash("sha256")
    .update(certificateId, "utf8")
    .digest("hex");

  const registry = await hre.ethers.getContractAt(
    "CertificateRegistry",
    contractAddress,
  );

  const existing = await registry.getCertificate(certificateIdHash);
  if (existing[3]) {
    if (existing[0].toLowerCase() !== documentHash.toLowerCase()) {
      throw new Error(
        "This Certificate ID is already anchored with a different file hash. Do not overwrite it.",
      );
    }
    console.log("Already anchored with the same document hash.");
    return;
  }

  const tx = await registry.anchorCertificate(certificateIdHash, documentHash);
  console.log("Anchor transaction:", tx.hash);
  await tx.wait();
  console.log("Certificate anchored:", certificateId);
  console.log("Document SHA-256:", documentHash);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
