# Blockchain module

The `CertificateRegistry` contract anchors a certificate identifier and SHA-256-derived document hash on-chain. No certificate file is stored on-chain.

## Setup

From this directory:

```bash
npm install
npm run compile
```

For Polygon Amoy deployment, create `blockchain/.env` from `.env.example` and add your own values:

```env
POLYGON_AMOY_RPC_URL=your_amoy_rpc_url
DEPLOYER_PRIVATE_KEY=your_dedicated_test_wallet_private_key
```

Never commit `.env` or share the private key.

## Deploy locally

### Option A — one-off local Hardhat network

This starts a temporary local blockchain, deploys the contract, and exits:

```bash
npm run deploy:local
```

The local deployment is useful for compiling and testing the contract without any faucet, RPC provider, or real/test funds.

### Option B — persistent local node

Terminal 1:

```bash
npm run node
```

Keep it running.

Terminal 2:

```bash
npm run deploy:localhost
```

## Deploy to Polygon Amoy

After the dedicated test wallet has Amoy POL:

```bash
npm run deploy:amoy
```

The script checks that the selected network is Polygon Amoy (chain ID 80002), checks the deployer balance, deploys `CertificateRegistry`, and prints the contract address.

That deployed address is the value used for Vercel's `BLOCKCHAIN_CONTRACT_ADDRESS`.

## Deployment flow

```text
Local Hardhat
    ↓
Compile + test contract
    ↓
Polygon Amoy
    ↓
Deploy CertificateRegistry
    ↓
Copy contract address
    ↓
Vercel BLOCKCHAIN_CONTRACT_ADDRESS
```
