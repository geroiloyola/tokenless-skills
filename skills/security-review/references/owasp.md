# OWASP Top 10 2021 checks

A01:2021-Broken Access Control → See Authz (step 4) and ensure object-level access control.
A02:2021-Cryptographic Failures → Check hardcoded secrets, weak algorithms, and missing encryption.
A03:2021-Injection → See step 3 (SQL, NoSQL, OS, XSS, SSRF).
A04:2021-Insecure Design → No "trust me" comments; validate all inputs and outputs.
A05:2021-Security Misconfiguration → Default credentials, verbose errors, exposed debug endpoints.
A06:2021-Vulnerable and Outdated Components → See Dependencies (step 6); use `npm audit` or `snyk test`.
A07:2021-Identification and Authentication Failures → Check auth flows for weak passwords, missing MFA, and session fixation.
A08:2021-Software and Data Integrity Failures → Verify signatures, hashes, and CI/CD integrity.
A09:2021-Logging Failures → Ensure sensitive data is not logged; check for PII in logs.
A10:2021-SSRF → See step 3 (user input in URLs for internal requests).

## Quick commands (heuristics — a match is a lead, not a finding)
- CSRF coverage: `grep -rniE "csrftoken|xsrf|samesite" <src>/` — if it returns nothing and the diff adds POST forms or cookie sessions, flag CSRF as likely missing and verify the framework's default (Django/Rails include it; Express does not).
- Mass assignment: `grep -rnE "\.(body|params)[^)]*\.(create|update|save|patch)" <src>/` — passing `req.body` whole into a write call without a field allowlist.
- SSRF: `grep -rnE "(fetch|axios|http\.request)\s*\(\s*[A-Za-z_$]*(url|host|origin|base)" <src>/` — trace whether the URL variable derives from user input.
