# Blockchain module

The `CertificateRegistry` contract anchors a certificate identifier and SHA-256-derived document hash on-chain. No certificate file is stored on-chain.

## Polygon Amoy

Set `POLYGON_AMOY_RPC_URL` and `DEPLOYER_PRIVATE_KEY` locally. Never commit either value. Then run:

```bash
npm install
npx hardhat compile
npx hardhat run scripts/deploy.js --network amoy
```

The resulting deployed contract address belongs in the backend environment as `BLOCKCHAIN_CONTRACT_ADDRESS` when blockchain integration is activated.
