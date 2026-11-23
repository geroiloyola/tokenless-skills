---
name: security-review
description: "Checks a diff for secrets, injection, authz gaps, unsafe deserialization and risky dependencies. Use before merges touching auth, payments, uploads or queries, or on request. Not for diffs with no trust boundary; not a pen-test."
license: MIT
metadata:
  version: "0.4.0"
---

# security-review

## Steps
1. Map the diff: does it touch input parsing, auth, permissions, payments, uploads, SQL/NoSQL, HTML rendering, file paths, env vars, or dependency manifests? If none, say "no trust boundary in scope" and stop.
2. Secrets: `git diff --name-only --diff-filter=d | xargs -r grep -nE "sk-|api[_-]?key|secret|token|password|BEGIN .*PRIVATE" --` (diff-filter=d skips deleted paths so grep does not error). This greps the touched files as they are now — pre-existing secrets will surface too; confirm a hit was added by this change with `git diff -U0 -- <file> | grep '^+'` before classifying. Check .env files are untracked and reasons for any new env var.
3. Injection: user input reaching SQL (concat/interp), shell, eval, innerHTML/dangerouslySetInnerHTML, template engines without escaping, path joins with untrusted segments.
   **CSRF**: forms without CSRF tokens or missing `SameSite=Lax` cookies.
4. Authz: every new endpoint has an auth check; object access verifies ownership, not only login state; no IDOR via sequential IDs; admin routes guarded server-side.
   **SSRF**: user input used in URLs for internal requests (fetch, axios, curl).
5. Data: mass assignment, unbounded queries, missing pagination on user-facing lists, error messages leaking stack traces or SQL.
   **Mass Assignment**: `update` endpoints without allowlist of fields.
6. Dependencies: new packages in the diff? report name, version, why; prefer existing deps. Run the repo's audit command only if it is already configured.
   **OWASP Top 10**: see `references/owasp.md` for full coverage.
7. Out of scope by default: Semgrep/CodeQL, pentesting, infra. Recommend them in the report if the risk justifies it.

## Rules
- Never fix by adding a sanitizer around badly-placed raw input; fix at the boundary.
- A finding without an exploit path is a MINOR, not a BLOCKER.
- Do not paste real secrets in the report; use the file:line and the prefix only.

## Output
`vector | file:line | exploit path | severity (BLOCKER/MAJOR/MINOR) | fix | verified`
