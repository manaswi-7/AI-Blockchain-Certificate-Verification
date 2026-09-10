# AI-Enhanced Blockchain-Based Academic Certificate Verification System

A full-stack academic certificate issuance and verification platform combining Next.js, Spring Boot, PostgreSQL, AI-assisted document analysis, Solidity blockchain anchoring, and QR verification.

## Current end-to-end flow

`Issuer → upload certificate → SHA-256 hash → blockchain anchor → QR → database`

`Verifier → Certificate ID / QR → optional file upload → SHA-256 → database + blockchain → result`

The actual certificate file is hashed; the blockchain stores only the certificate key and document hash. No fake transactions are generated.

## Run locally

### 1. Start PostgreSQL and AI service

From the repository root:

```bash
docker compose up -d --build
```

PostgreSQL runs on `localhost:5432` and the AI service on `localhost:8000`.

If you do not use Docker for AI, run it from `ai-service` with Python 3.11+ and `uvicorn app:app --reload --port 8000`.

### 2. Start a local blockchain

Open a second terminal:

```bash
cd blockchain
npm install
npx hardhat node
```

Keep this terminal running. Hardhat prints funded development accounts and private keys.

Open a third terminal and deploy the registry:

```bash
cd blockchain
npm install
npx hardhat compile
npx hardhat run scripts/deploy.js --network hardhat
```

Copy the deployed contract address. For a persistent local node, use `--network localhost` instead:

```bash
npx hardhat run scripts/deploy.js --network localhost
```

### 3. Configure Spring Boot

Set these environment variables in your terminal (PowerShell example):

```powershell
$env:POLYGON_AMOY_RPC_URL="http://127.0.0.1:8545"
$env:BLOCKCHAIN_PRIVATE_KEY="PASTE_THE_PRIVATE_KEY_FROM_HARDHAT_NODE"
$env:BLOCKCHAIN_CONTRACT_ADDRESS="PASTE_THE_DEPLOYED_CONTRACT_ADDRESS"
$env:BLOCKCHAIN_CHAIN_ID="31337"
$env:VERIFICATION_URL="http://localhost:3000/verify"
$env:AI_SERVICE_URL="http://localhost:8000"
```

The variable name `POLYGON_AMOY_RPC_URL` is retained for compatibility; the local test network is Hardhat chain ID 31337.

### 4. Start the backend

```bash
cd backend
mvn spring-boot:run
```

Backend: `http://localhost:8080`

### 5. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Create an issuer for local testing

Public registration creates only a VERIFIER account. For local testing, create an issuer using the protected setup endpoint:

```powershell
curl.exe -X POST http://localhost:8080/api/auth/register-issuer `
  -H "Content-Type: application/json" `
  -H "X-Setup-Key: local-setup-key-change-me" `
  -d '{"fullName":"Test Issuer","email":"issuer@example.com","password":"Password123"}'
```

Then use the issuer email/password on the website login page.

For anything beyond local development, set a strong `app.setup-key`/`SETUP_KEY` equivalent and remove or disable this setup route.

## Test the complete flow

1. Login as the issuer.
2. Enter a unique certificate ID, recipient, course, institution and issue date.
3. Upload the real PDF/PNG/JPG certificate.
4. Click **Issue securely**.
5. The backend hashes the uploaded bytes, sends a real transaction to the configured blockchain, stores the transaction reference, and generates a QR code.
6. Click **Verify** beside the issued certificate or open the QR destination.
7. The verification page checks the database hash and blockchain record.
8. Upload the exact same certificate file: result should be `GENUINE`.
9. Change even one byte/file and upload it with the same Certificate ID: result should be `TAMPERED`.
10. Try an unknown Certificate ID: result should be `INVALID`.

## Important

The AI service is advisory and never replaces cryptographic or blockchain verification. The current local AI implementation provides OCR/field analysis where supported; blockchain and file hashing remain the source of truth for authenticity.

## Structure

```text
frontend/     Next.js + TypeScript + Tailwind
backend/      Spring Boot + Java + Spring Security
ai-service/   FastAPI + OCR/analysis service
blockchain/   Solidity + Hardhat
database/     PostgreSQL schema
```
