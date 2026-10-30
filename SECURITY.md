# Security Policy

## 1. Scope & Commitment

AnimeBridge is committed to the security of its users and the integrity of the open-source software ecosystem. We take potential vulnerabilities, data leaks, and insecure data handling seriously.

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability or sensitive data leak in this repository, please **do not report it publicly in GitHub issues**.

Instead, report it responsibly via:
- **GitHub Security Advisory**: Navigate to the **Security** tab of this repository and select **Report a vulnerability**.
- **Email**: `security@animebridge.org` (or contact project maintainers directly).

Please include:
- A detailed description of the vulnerability.
- Steps to reproduce or proof-of-concept payload.
- Affected extensions, versions, or scripts.
- Any potential impact on users.

We will acknowledge receipt within 48 hours and work with you on a coordinated disclosure timeline.

---

## 3. Secrets Handling & Integrity Guidelines

To protect user privacy and system security:

1. **No Hardcoded Credentials**:
   Never commit passwords, private API keys, session cookies, Bearer tokens, or personal viewing histories to source code.
2. **Dynamic Code Execution**:
   Extensions must compile to static bytecode. Dynamic downloading of remote DEX files or executing unverified remote JavaScript via `eval()` is strictly prohibited.
3. **Traffic Integrity**:
   All network requests to remote media catalogs and API endpoints must use HTTPS with valid TLS certificates. Insecure plaintext HTTP is only permitted when connecting to local network proxies (e.g., `http://127.0.0.1` or `http://localhost`).
4. **Input Sanitization**:
   All user queries, search parameters, and remote JSON/HTML payloads must be safely encoded to prevent injection attacks and memory exhaustion.
