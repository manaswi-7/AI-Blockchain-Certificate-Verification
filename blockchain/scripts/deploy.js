const hre = require("hardhat");
async function main() {
  const Factory = await hre.ethers.getContractFactory("CertificateRegistry");
  const registry = await Factory.deploy();
  await registry.waitForDeployment();
  console.log("CertificateRegistry:", await registry.getAddress());
}
main().catch((error)=>{console.error(error);process.exitCode=1;});
