const hre = require("hardhat");

async function main() {
  const networkName = hre.network.name;
  const network = await hre.ethers.provider.getNetwork();
  const chainId = network.chainId;

  console.log("Network:", networkName);
  console.log("Chain ID:", chainId.toString());

  if (networkName === "amoy") {
    if (!process.env.POLYGON_AMOY_RPC_URL) {
      throw new Error(
        "POLYGON_AMOY_RPC_URL is missing. Add it to blockchain/.env before deploying to Amoy.",
      );
    }

    if (!process.env.DEPLOYER_PRIVATE_KEY) {
      throw new Error(
        "DEPLOYER_PRIVATE_KEY is missing. Add your dedicated test-wallet private key to blockchain/.env.",
      );
    }

    if (chainId !== 80002n) {
      throw new Error(
        `Wrong network. Expected Polygon Amoy (80002), received ${chainId}.`,
      );
    }
  } else if (networkName === "hardhat" || networkName === "localhost") {
    if (chainId !== 31337n) {
      throw new Error(
        `Unexpected local chain ID. Expected 31337, received ${chainId}.`,
      );
    }
  } else {
    throw new Error(
      `Unsupported deployment network: ${networkName}. Use --network hardhat, --network localhost, or --network amoy.`,
    );
  }

  const [deployer] = await hre.ethers.getSigners();

  if (!deployer) {
    throw new Error(
      networkName === "localhost"
        ? "No local account is available. Start 'npx hardhat node' in another terminal and try again."
        : "No deployer account is available.",
    );
  }

  const address = await deployer.getAddress();
  const balance = await hre.ethers.provider.getBalance(address);

  console.log("Deployer:", address);
  console.log(
    "Balance:",
    hre.ethers.formatEther(balance),
    networkName === "amoy" ? "POL" : "ETH",
  );

  if (balance === 0n) {
    throw new Error(
      networkName === "amoy"
        ? "Deployer wallet has 0 POL on Polygon Amoy. Add Amoy test POL and run the deployment again."
        : "Deployer account has 0 balance.",
    );
  }

  console.log("Compiling/deploying CertificateRegistry...");

  const Factory = await hre.ethers.getContractFactory("CertificateRegistry");
  const registry = await Factory.deploy();

  const deploymentTx = registry.deploymentTransaction();
  console.log("Deployment transaction:", deploymentTx?.hash || "pending");

  await registry.waitForDeployment();

  const contractAddress = await registry.getAddress();

  console.log("CertificateRegistry:", contractAddress);
  if (networkName === "amoy") {
    console.log(
      "Explorer:",
      `https://amoy.polygonscan.com/address/${contractAddress}`,
    );
  }
  console.log("Deployment completed successfully.");
}

main().catch((error) => {
  console.error("\nDEPLOYMENT FAILED\n");
  console.error(error);
  process.exitCode = 1;
});
