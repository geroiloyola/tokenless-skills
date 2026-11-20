# Security Policy

## Supported scope

- The security-relevant surface of this repository is: `install.sh` (runs on your machine), and `extras/vibe/guard.py` + `extras/vibe/qa.py` (run as hooks on every matching tool call).
- The skills themselves are markdown instructions; they cannot execute anything by themselves in hosts that treat prompts as data.

## Known limitations (read first)

`docs/SECURITY.md` documents exactly what the guard catches, what it fails open on, and which bypass shapes remain. Please read it before filing — most "the guard can be bypassed by X" reports will already be listed, and listed is the correct state for a pattern-based tripwire.

## Reporting a vulnerability

Open a private security advisory via GitHub ("Security" → "Report a vulnerability") or contact the repository owner directly. Please include the exact payload, the mode (`bash`/`protect`), and the observed vs expected behavior.

- Non-destructive reproductions only; do not demonstrate against anyone's real environment.
- Please do not open public issues for actionable bypasses before a patch window (48–72h).

## What we will/won't consider a vulnerability

- ✅ In scope: data loss you can trigger through documented installer usage; guard denials/allowances that contradict `docs/SECURITY.md`; execution of arbitrary code during installation beyond `git clone` + running `install.sh`.
- ❌ Out of scope: the guard's documented bypass classes; the host agent's own security model; social engineering of a user through skill instructions (that is prompt-injection, the host's defense is approval modes).
