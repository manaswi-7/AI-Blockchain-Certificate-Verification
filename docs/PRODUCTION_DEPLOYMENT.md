# Production deployment

This repository is a monorepo, so deploy the three runtime pieces separately:

1. Next.js frontend → Vercel
2. Spring Boot API → Koyeb
3. FastAPI AI service → Koyeb
4. PostgreSQL → Supabase

Koyeb supports GitHub deployments and monorepo work directories. Set the work directory to the service folder when creating each service.

## 1. Supabase PostgreSQL

Create a Supabase project and open **Connect → Session pooler**. Use the connection values from Supabase; do not invent the hostname.

Set these backend variables:

```text
DB_URL=jdbc:postgresql://<pooler-host>:5432/postgres?sslmode=require
DB_USERNAME=<supabase-pooler-username>
DB_PASSWORD=<supabase-password>
```

The Spring Boot application automatically runs `schema.sql` on startup.

## 2. Deploy the AI service

In Koyeb:

- Create Web Service
- GitHub repository: `manaswi-7/AI-Blockchain-Certificate-Verification`
- Branch: `main`
- Work directory: `ai-service`
- Builder: Dockerfile
- Exposed port: `8000`
- Route: `/`

The AI service Dockerfile already uses Koyeb's `PORT` variable.

After deployment, copy the public AI URL, for example:

```text
https://<your-ai-service>.koyeb.app
```

## 3. Deploy the Spring Boot backend

Create another Koyeb Web Service from the same GitHub repository:

- Branch: `main`
- Work directory: `backend`
- Builder: Dockerfile
- Exposed port: `8080`
- Route: `/`

Set:

```text
FRONTEND_URL=https://ai-blockchain-certificate-verificat.vercel.app
DB_URL=jdbc:postgresql://<supabase-pooler-host>:5432/postgres?sslmode=require
DB_USERNAME=<supabase-pooler-username>
DB_PASSWORD=<supabase-password>
JWT_SECRET=<long-random-secret>
SETUP_KEY=<long-random-setup-key>
AI_SERVICE_URL=https://<your-ai-service>.koyeb.app
VERIFICATION_URL=https://ai-blockchain-certificate-verificat.vercel.app/verify
BLOCKCHAIN_RPC_URL=<polygon-amoy-rpc-url>
BLOCKCHAIN_PRIVATE_KEY=<issuer-wallet-private-key>
BLOCKCHAIN_CONTRACT_ADDRESS=<deployed-registry-contract>
BLOCKCHAIN_CHAIN_ID=80002
```

Never commit these values to GitHub.

Check:

```text
https://<your-backend>.koyeb.app/api/health
```

It should return:

```json
{"status":"UP","service":"certificate-verification-api"}
```

## 4. Configure Vercel

In the Vercel project for the frontend, open:

**Settings → Environment Variables**

Add for **Production**:

```text
NEXT_PUBLIC_API_URL=https://<your-backend>.koyeb.app/api
```

Then redeploy the frontend.

Do not put a trailing slash after `/api`.

## 5. Blockchain

The backend expects a real deployed registry contract for blockchain verification.

For Polygon Amoy:

- deploy the contract from `blockchain/`
- use chain ID `80002`
- fund the issuer/deployer wallet with Amoy test MATIC
- copy the deployed contract address into `BLOCKCHAIN_CONTRACT_ADDRESS`

Do not commit the wallet private key.

## Important

A frontend-only Vercel deployment cannot make the Spring Boot API appear automatically. The `Verification backend is not configured for this deployment` message occurs when `NEXT_PUBLIC_API_URL` is missing.

The frontend code is already prepared for the production API. The missing production pieces are external services and their secrets, which must be connected through your own Vercel/Koyeb/Supabase accounts.

## References

- Koyeb GitHub deployment: https://www.koyeb.com/docs/build-and-deploy/deploy-with-git
- Koyeb monorepos: https://www.koyeb.com/docs/build-and-deploy/monorepo
- Supabase PostgreSQL connections: https://supabase.com/docs/guides/database/connecting-to-postgres
