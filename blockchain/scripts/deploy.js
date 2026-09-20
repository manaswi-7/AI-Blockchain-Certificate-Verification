const hre = require("hardhat");

async function main() {
  const rpcUrl = process.env.POLYGON_AMOY_RPC_URL;
  const privateKey = process.env.DEPLOYER_PRIVATE_KEY;

  if (!rpcUrl) {
    throw new Error("POLYGON_AMOY_RPC_URL is missing.");
  }

  if (!privateKey) {
    throw new Error("DEPLOYER_PRIVATE_KEY is missing.");
  }

  const network = await hre.ethers.provider.getNetwork();

  console.log("Network:", network.name || "unknown");
  console.log("Chain ID:", network.chainId.toString());

  if (network.chainId !== 80002n) {
    throw new Error(
      `Wrong network. Expected Polygon Amoy (80002), received ${network.chainId}.`,
    );
  }

  const [deployer] = await hre.ethers.getSigners();

  if (!deployer) {
    throw new Error("No deployer account was loaded from DEPLOYER_PRIVATE_KEY.");
  }

  const address = await deployer.getAddress();
  const balance = await hre.ethers.provider.getBalance(address);

  console.log("Deployer:", address);
  console.log("Balance:", hre.ethers.formatEther(balance), "MATIC");

  if (balance === 0n) {
    throw new Error(
      "Deployer wallet has 0 MATIC on Polygon Amoy. Add Amoy test MATIC and run the workflow again.",
    );
  }

  console.log("Compiling/deploying CertificateRegistry...");

  const Factory = await hre.ethers.getContractFactory("CertificateRegistry");
  const registry = await Factory.deploy();

  console.log("Deployment transaction:", registry.deploymentTransaction()?.hash);

  await registry.waitForDeployment();

  const contractAddress = await registry.getAddress();

  console.log("CertificateRegistry:", contractAddress);
  console.log("Deployment completed successfully.");
}

main().catch((error) => {
  console.error("\nDEPLOYMENT FAILED\n");
  console.error(error);
  process.exitCode = 1;
});
