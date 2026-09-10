# Deployment checklist

## 1. AI service
- Train `certificate_generation/train_tamper_model.py`.
- Copy the resulting `certificate_tamper_model.keras` into `ai-service/models/`.
- Add TensorFlow to the AI service runtime requirements before enabling model inference.
- Verify `/health` and `/analyze` with a real image.

## 2. Blockchain
- Configure a Polygon Amoy RPC endpoint.
- Fund a deployment/issuer wallet with Amoy test POL.
- Deploy `CertificateRegistry.sol` with Hardhat.
- Set `BLOCKCHAIN_RPC_URL`, `BLOCKCHAIN_PRIVATE_KEY`, `BLOCKCHAIN_CONTRACT_ADDRESS`, and `BLOCKCHAIN_CHAIN_ID=80002` in the backend environment.
- Never commit the private key.

## 3. Database
- Create PostgreSQL database.
- Run the backend schema initialization.
- Set `DB_URL`, `DB_USERNAME`, and `DB_PASSWORD` as deployment secrets.

## 4. Backend
- Set a long random `JWT_SECRET`.
- Set `AI_SERVICE_URL` to the deployed AI service.
- Set `VERIFICATION_URL` to the deployed frontend verification route.
- Start Spring Boot and check `/api/health`.

## 5. Frontend
- Set the backend API base URL according to the frontend implementation.
- Deploy Next.js to Vercel or another supported host.
- Verify public upload verification and authenticated issuer flows.

## 6. End-to-end test
1. Issue one genuine certificate.
2. Confirm the blockchain transaction succeeds.
3. Upload the exact original image and expect `VERIFIED`.
4. Modify the image and upload it; expect hash mismatch / `INVALID` or the appropriate AI warning path.
5. Upload an unregistered certificate; expect `INVALID` / `NOT_REGISTERED`.
6. Scan the QR code and confirm the verification page resolves.
7. Record transaction hash, model metrics, screenshots, and test results for the report.
