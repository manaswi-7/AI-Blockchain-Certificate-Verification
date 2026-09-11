# AI-Enhanced Blockchain-Based Academic Certificate Verification System

A full-stack academic certificate issuance and verification platform combining Next.js, Spring Boot, PostgreSQL, AI-assisted document analysis, Solidity blockchain anchoring, and QR verification.

## Current end-to-end flow

`Issuer → upload certificate → SHA-256 hash → blockchain anchor → QR → database`

`Verifier → upload certificate → OCR → AI analysis → SHA-256 → database + blockchain → result`

The actual certificate file is hashed; the blockchain stores only the certificate key and document hash. No fake transactions are generated.

## Run locally

### 1. Start PostgreSQL and AI service

From the repository root:

```bash
docker compose up -d --build
```

PostgreSQL runs on `localhost:5432` and the AI service on `localhost:8000`.

If you do not use Docker for AI, run it from `ai-service` with Python 3.10+ and `uvicorn app:app --reload --port 8000`.

### 2. Start a local blockchain

Open a second terminal:

```bash
cd blockchain
npm install
npx hardhat node
```

Keep this terminal running. Hardhat prints funded development accounts and private keys. Never publish a development private key or use it for real funds.

Open a third terminal and deploy the registry:

```bash
cd blockchain
npm install
npx hardhat compile
npx hardhat run scripts/deploy.js --network localhost
```

Copy the deployed contract address.

### 3. Configure Spring Boot

Set these environment variables in your terminal (PowerShell example):

```powershell
$env:BLOCKCHAIN_RPC_URL="http://127.0.0.1:8545"
$env:BLOCKCHAIN_PRIVATE_KEY="PASTE_THE_PRIVATE_KEY_FROM_HARDHAT_NODE"
$env:BLOCKCHAIN_CONTRACT_ADDRESS="PASTE_THE_DEPLOYED_CONTRACT_ADDRESS"
$env:BLOCKCHAIN_CHAIN_ID="31337"
$env:VERIFICATION_URL="http://localhost:3000/verify"
$env:AI_SERVICE_URL="http://localhost:8000"
$env:FRONTEND_URL="http://localhost:3000"
```

For Polygon Amoy deployment, use your Polygon Amoy RPC URL, funded deployer/issuer wallet, deployed contract address, and chain ID `80002` instead.

### 4. Start the backend

```bash
cd backend
mvn spring-boot:run
```

Backend health check: `http://localhost:8080/api/health`

### 5. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

For a deployed frontend, set the Vercel environment variable `NEXT_PUBLIC_API_URL` to the public Spring Boot API base URL ending in `/api`, for example `https://your-backend.example.com/api`. Do not use `localhost` in a production deployment.

## Create an issuer for local testing

Public registration creates only a VERIFIER account. For local testing, create an issuer using the protected setup endpoint:

```powershell
curl.exe -X POST http://localhost:8080/api/auth/register-issuer `
  -H "Content-Type: application/json" `
  -H "X-Setup-Key: local-setup-key-change-me" `
  -d '{"fullName":"Test Issuer","email":"issuer@example.com","password":"Password123"}'
```

Then use the issuer email/password on the website login page.

For anything beyond local development, set a strong `SETUP_KEY` and keep it out of source control.

## Test the complete flow

1. Login as the issuer.
2. Enter a unique certificate ID, recipient, course, institution and issue date.
3. Upload a genuine PNG/JPEG certificate.
4. Click **Issue securely**.
5. The backend hashes the uploaded bytes, sends a real transaction to the configured blockchain, stores the transaction reference, and generates a QR code.
6. Click **Verify** beside the issued certificate or open the QR destination.
7. Upload the exact same certificate image on the verification page.
8. A matching SHA-256 hash and blockchain record can produce `VERIFIED` when AI also reports genuine, or `VERIFIED_WITHOUT_AI` when AI is unavailable.
9. A changed file produces a hash mismatch and should be reported as `INVALID`.
10. An unknown Certificate ID produces `INVALID` or `UNVERIFIED` depending on the service state.

## Important

The AI service is advisory and never replaces cryptographic or blockchain verification. The AI service provides OCR/field analysis and uses a trained tamper model only when the model file is actually available. Blockchain and file hashing remain the source of truth for cryptographic authenticity.

## Production deployment

The repository includes `render.yaml` for a Spring Boot API and AI service. The API also exposes `/api/health` for deployment health checks.

The frontend can be deployed on Vercel. After the backend is deployed, configure `NEXT_PUBLIC_API_URL` in the Vercel project and redeploy. The backend must allow the exact Vercel origin through `FRONTEND_URL`.

Required production backend variables include:

- `DB_URL`
- `DB_USERNAME`
- `DB_PASSWORD`
- `JWT_SECRET`
- `SETUP_KEY`
- `AI_SERVICE_URL`
- `VERIFICATION_URL`
- `FRONTEND_URL`
- `BLOCKCHAIN_RPC_URL`
- `BLOCKCHAIN_PRIVATE_KEY`
- `BLOCKCHAIN_CONTRACT_ADDRESS`
- `BLOCKCHAIN_CHAIN_ID`

Never commit passwords, JWT secrets, wallet private keys, or RPC credentials.

## Structure

```text
frontend/     Next.js + TypeScript + Tailwind
backend/      Spring Boot + Java + Spring Security
ai-service/   FastAPI + OCR/analysis service
blockchain/   Solidity + Hardhat
database/     PostgreSQL schema
```
