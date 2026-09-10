# AI-Enhanced Blockchain-Based Academic Certificate Verification System

A full-stack academic certificate issuance and verification platform combining Spring Boot, PostgreSQL, AI-assisted document analysis, Solidity blockchain anchoring, and QR-based verification.

## Architecture

`Next.js Web App → Spring Boot API → PostgreSQL`

`                         ↘ AI Service`

`                         ↘ Blockchain`

The blockchain stores a cryptographic document/data hash and certificate reference. Certificate files and application metadata remain off-chain.

## Planned modules

- Role-based authentication: Admin, Issuer, Verifier
- Institution and user management
- Certificate issuance and secure hashing
- AI-assisted OCR/field extraction and consistency checks
- Blockchain hash anchoring and verification
- QR-code verification
- Certificate search and verification history
- Admin dashboard and reports
- Validation, error handling, audit logging and secure configuration

## Repository structure

```text
frontend/     Next.js + TypeScript + Tailwind
backend/      Spring Boot + Java + Spring Security + JPA
ai-service/   FastAPI + OCR/analysis service
blockchain/   Solidity + Hardhat
 database/     PostgreSQL schema and seed SQL
docs/         Architecture and API documentation
```

## Status

Initial production-oriented scaffold. External credentials and deployment settings are intentionally supplied through environment variables; no fake blockchain transactions or AI results are used.

## Local prerequisites

- Java 21+
- Node.js 20+
- Python 3.11+
- PostgreSQL 16+
- Node/npm
- Optional: Hardhat/Polygon Amoy wallet for blockchain activation

See each module README for setup details.
