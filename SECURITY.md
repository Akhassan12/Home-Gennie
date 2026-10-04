# Security Policy

The Home Gennie team takes the security and integrity of user data, AI pipelines, and platform infrastructure seriously. This document outlines our vulnerability disclosure process and the security architecture implemented across the application.

---

## Supported Versions

Security updates and patches are actively maintained for the current release branch.

| Version | Supported | Status |
| ------- | --------- | ------ |
| `2.x` (`main` branch) | :white_check_mark: | Active support |
| `< 2.0` | :x: | End of Life (Unsupported) |

---

## Reporting a Vulnerability

If you discover a security vulnerability in Home Gennie, please report it responsibly. **Do not create public GitHub issues for security vulnerabilities.**

### How to Report

1. **Email:** Send details directly to `hasanqadri1990@gmail.com` with the subject line `[SECURITY] Home Gennie Vulnerability Report`.
2. **GitHub Security Advisories:** Alternatively, submit a private advisory through the GitHub repository under **Security > Advisories > Report a vulnerability**.

### What to Include

To help us triage and resolve the issue quickly, please provide:
- A clear description of the vulnerability.
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- The affected component (e.g., FastAPI backend, React frontend, database RLS, storage bucket).
- Potential impact and severity assessment.
- Any suggested fixes or mitigations.

### Response Timeline

- **Initial Acknowledgment:** Within **48 hours** of report receipt.
- **Triage & Status Update:** Within **5 business days** confirming vulnerability status.
- **Remediation & Patching:** A fix will be developed, tested, and released as quickly as feasible.
- **Coordinated Disclosure:** We kindly request that you allow sufficient time for remediation prior to any public disclosure.

---

## Security Architecture & Best Practices

Home Gennie is engineered with multiple layers of defense-in-depth:

### 1. Database Row-Level Security (RLS)
- PostgreSQL Row-Level Security is strictly enabled on sensitive tables, including `public.designs` and `public.profiles`.
- Authenticated users can only query, insert, update, or delete records that match their verified identity (`auth.uid() = user_id`).
- Direct client manipulation or tampering through Supabase REST endpoints cannot access or modify another user's project history.
- See [`secure_database_policies.sql`](secure_database_policies.sql) for exact policy rules.

### 2. Cloud Storage Isolation
- Dedicated storage buckets (`uploads`, `designs`, `models`) enforce user-scoped path policies.
- Users are restricted to write, modify, and delete files solely within their user-specific directory (`{user_id}/`).
- This prevents cross-tenant file tampering and unauthorized asset overwrites.
- See [`secure_storage_policies.sql`](secure_storage_policies.sql) for storage access definitions.

### 3. Identity & Token Verification
- Client authentication is managed via Supabase Auth using cryptographically signed JSON Web Tokens (JWTs).
- All requests to the FastAPI backend include the user's session token via `Authorization: Bearer <jwt>`.
- The backend verifies and passes through user context, ensuring database and storage actions remain bounded by user permissions.

### 4. Privilege Separation & Secrets Management
- The high-privilege `SUPABASE_SERVICE_KEY` is exclusively restricted to the backend server environment and is never included in client-side bundles.
- The frontend only contains the public anonymous key (`VITE_SUPABASE_ANON_KEY`), protected by database RLS.
- Sensitive environment files (`.env`, `.env.local`) are explicitly excluded from version control via `.gitignore`.

### 5. CORS Hardening
- The FastAPI backend enforces an explicit CORS whitelist allowing only trusted development hosts and the production `FRONTEND_URL`.
- Permissive wildcard origins (`*`) are disallowed, mitigating Cross-Origin Resource Sharing exploits.

### 6. Container Security
- The backend Docker container runs under an unprivileged non-root user (`UID 1000`).
- Container builds isolate execution permissions and follow minimal privilege principles for cloud environments.

### 7. Asset Permanence & Pipeline Validation
- Temporary or expiring CDN URLs from upstream AI services (e.g., Replicate, AI Horde) are never trusted for long-term storage.
- The backend fetches and verifies image and model bytes, then re-uploads them into authenticated cloud storage buckets, eliminating link hijacking risks.

---

## Guidelines for Self-Hosters

If you are self-hosting or deploying an instance of Home Gennie:

1. Always apply both `secure_database_policies.sql` and `secure_storage_policies.sql` to your Supabase project before public launch.
2. Ensure `FRONTEND_URL` is set strictly to your production domain to keep CORS protections active.
3. Keep third-party API tokens secure and regenerate credentials immediately if accidentally exposed.
