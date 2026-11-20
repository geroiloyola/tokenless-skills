#!/usr/bin/env python3
"""Security guard for AI agent tool hooks (e.g. Mistral Vibe hooks.toml).

IMPORTANT SCOPE: this is a best-effort *accident guard*, not a sandbox and
not a security boundary. It blocks common destructive mistakes by pattern;
it cannot stop a determined bypass (command construction, obfuscation,
interpreters). Defense in depth still requires OS permissions, containers,
and the host's own approval mechanisms.

Modes (passed as argv[1]):
  bash     -> pre_tool hook for shell tools: blocks destructive commands.
  protect  -> pre_tool hook for write/edit tools: blocks writes to secrets
              and critical files. FAILS CLOSED on malformed input: if the
              guard cannot tell what file is being written, it denies and
              asks the host/user for explicit confirmation. Valid harmless
              writes are never affected.

Contract (Vibe-style hooks): JSON payload on stdin; JSON response on stdout.
  exit 0 + {"decision":"deny","reason":"..."}  -> block
  exit 0 + empty stdout                        -> allow (passthrough)
"""

import json
import os
import re
import sys

# --- destructive command patterns (compiled case-insensitive; input is also
# normalized: quotes are treated as neutral characters so `rm -rf "$HOME"`
# is normalized to the same string as `rm -rf $HOME`) -----------------------
DANGEROUS = [
    # rm catastrophic targets. Depth policy: bare root, home tilde, and
    # $HOME forms deny; deeper relative/home subpath deletes stay allowed so
    # normal dev work (rm -rf ~/.cache/pip, rm -rf ./build) is not blocked.
    (r"\brm\s+(?:-\w+\s+)+(/\*|/)(/|\s|$)", "recursive delete of the root or root glob"),
    (r"\brm\s+(?:-\w+\s+)+~\w*/?(\s|$)", "recursive delete of a home directory"),
    (r"\brm\s+(?:-\w+\s+)+\$@?\{?home\}?/?(\s|$)", "recursive delete of your home directory"),
    (r"\brm\s+(?:-\w+\s+)+\*(/|\s|$)", "wildcard delete"),
    (r"\brm\s+(?:-\w+\s+)+\.\.?/?(\s|$)", "recursive delete of the current or parent directory"),
    (r"\brm\s+(?:-\w+\s+)+\.git/?(\s|$)", "recursive delete of .git"),
    # depth-1 system dirs (rm -rf /home, /etc, ...) and drive-mount roots (/c/,
    # Windows C:/ or C:/Users) — depth-2+ paths stay allowed for normal work.
    (r"\brm\s+(?:-\w+\s+)+/(?:home|etc|usr|var|opt|boot|bin|sbin|lib|proc|sys|dev)\b(/?)(\s|$)",
     "recursive delete of a system directory"),
    (r"\brm\s+(?:-\w+\s+)+/[cd]\b(/?)(\s|$)", "recursive delete of a drive mount root"),
    (r"\brm\s+(?:-\w+\s+)+[a-z]:/?(\s|$)", "recursive delete of a whole drive"),
    (r"\brm\s+(?:-\w+\s+)+[a-z]:/(?:users|windows|program files)\b", "recursive delete of a Windows system directory"),
    # --no-preserve-root: long flag can't be matched by the -w flag group
    (r"\brm\b[^;&|\n]*--no-preserve-root", "rm with --no-preserve-root"),
    (r"\brm\s+(?:-\w+\s+)+(\$|\s|)\(", "rm targeting a command substitution"),
    (r"\brm\s+(?:-\w+\s+)+`\s*rm\s", "rm targeting a backtick substitution"),
    # wildcard/root deletes regardless of spelling (e.g. cd / && rm -rf *)
    (r"\bcd\s+/\s*(&&|;)\s*rm\s+", "change to root, then delete"),
    (r"\brm\s+-\w+\s+\*\s*$", "wildcard delete of the current directory"),
    (r"\brm\s+-\w+\s+\.\s*$", "delete the current directory"),
    (r"\bfind\s+(/\s*|~\s*)(?:.*)\bdelete\b", "find -delete (delete via find)"),
    # relative find deletion: deny -delete on . / bare find UNLESS a narrowing
    # -name/-iname/-regex predicate is present (keeps `find . -name '*.pyc' -delete` legal)
    (r"\bfind\s+\.?\s*(?![^;&|\n]*-(?:name|iname|regex)\b)[^;&|\n]*\s-delete\b",
     "find -delete on the current directory tree (no -name filter)"),
    (r"\bmkfs\b", "make filesystem (disk wipe)"),
    (r"\bdd\b[^;&|\n]*\bof=/dev/(?!null)", "write directly to a block device"),
    (r"\bshred\b[^;&|\n]*/dev/(?!null)", "shred a block device"),
    (r":\(\)\s*\{\s*:\|\s*:\s*&\s*\}\s*;", "fork bomb"),
    # chmod 777 with ANY flag arrangement including none (chmod -R 777 /, chmod 777 /, chmod 777 -R /)
    (r"\bchmod\s+(?:-\w+\s+)*777\b", "chmod 777"),
    (r">\s*/dev/sd[a-z]", "raw disk write redirection"),
    # force pushes: force-with-lease=false first (disables the lease), then
    # classic flags (incl. -ff shorthand), then the +refspec form
    (r"\bgit\s+push\b[^;&|\n]*--force-with-lease=(false|no)\b", "force push with lease disabled"),
    (r"\bgit\s+push\b(?![^;&|\n]*--force-with-lease\b)[^;&|\n]*(--force\b|\s-f{1,2}\b)", "git push --force without lease"),
    (r"\bgit\s+push\b[^;&|\n]*\s\+[\w\.]+", "force push via +refspec"),
    (r"\bgit\s+reset\s+--hard\b[^;&|\n]*\borigin\b", "reset --hard against origin"),
    (r"\bgit\s+clean\s+-[a-z]*[xdf]", "git clean (destructive)"),
    (r"\bgit\s+checkout\s+--\s+\.", "git checkout -- . (discard all local changes)"),
    # remote code execution shapes
    (r"\b(curl|wget)\b[^\n]*\|\s*(ba|z|da|k)?sh\b", "pipe remote content to a shell"),
    (r"\b(curl|wget)\b[^\n]*\|\s*(node|deno|bun|perl|ruby)\b", "pipe remote content to an interpreter"),
    (r"\b(ba|z|da|k)?sh\s+<\(\s*(curl|wget)\b", "execute downloaded script via process substitution"),
    (r"\beval\s+(\"|'|)\$\((curl|wget)\b", "eval of downloaded content"),
    (r"\b(curl|wget)\b[^\n]*\|\s*python(3)?\b", "pipe remote content to python"),
    # publishing / SQL
    (r"\bnpm\s+publish\b(?!.*--dry-run)|\btwine\s+upload\b|\bcargo\s+publish\b", "package publication"),
    (r"\bdrop\s+(database|table)\b", "SQL DROP"),
    (r"\btruncate\s+table\b", "SQL TRUNCATE"),
]

# Command-substitution children are checked too: `rm -rf $(...)` or
# `curl <$(reveal-secrets)` — if the substitution body itself looks
# destructive/remote, deny. Bodies are extracted and rescanned.
SUBSTITUTION = re.compile(r"\$\((.*?)\)|`(.*?)`", re.S)

# --- protected paths (compiled case-insensitive; backslashes normalized) ----
PROTECTED_PATHS = [
    (r"(^|/)\.env(\.[\w.\-]+)?$", "a .env file (secrets)"),
    (r"(^|/)\.?secrets?\.(env|key)$", "a secrets file"),
    (r"(^|/)\.git/|^\.git$", "inside .git"),
    (r"(^|/)\.ssh/", "inside ~/.ssh"),
    (r"(^|/)(id_rsa|id_dsa|id_ecdsa|id_ed25519)(\).\w+)?$", "an SSH private key"),
    (r"(^|/)(\.netrc|\.npmrc|\.pypirc)$", "a credentials file"),
    (r"(^|/)\.aws/", "AWS credentials"),
    (r"(^|/)\.kube/config$", "a Kubernetes cluster config"),
    (r"(^|/)\.docker/config\.json$", "Docker registry credentials"),
    (r"(^|/)\.gnupg/", "a GPG keyring"),
    (r"(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock|cargo\.lock|uv\.lock|go\.sum)$",
     "a lockfile (regenerate with the package manager, do not hand-edit)"),
]


def respond(decision=None, reason=None):
    out = {}
    if decision:
        out["decision"] = decision
    if reason:
        out["reason"] = reason
    print(json.dumps(out))
    sys.exit(0)


def deny(reason):
    respond(decision="deny", reason=reason)


def get_command(payload):
    ti = payload.get("tool_input") or {}
    if isinstance(ti, str):
        return ti
    for key in ("command", "cmd", "script"):
        if isinstance(ti, dict) and isinstance(ti.get(key), str):
            return ti[key]
    return ""


def get_path(payload):
    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        return ""
    for key in ("path", "file_path", "filename", "target"):
        if isinstance(ti.get(key), str):
            return ti[key]
    return ""


def normalize(text):
    # quotes and backslashes are neutral for our detection purposes; keep
    # everything else verbatim (conservative normalization).
    text = text.replace("\\", "/")
    for ch in "\"'`":
        text = text.replace(ch, " ")
    return text


def check_dangerous(text):
    low = normalize(text).lower()
    for pattern, label in DANGEROUS:
        if re.search(pattern, low):
            return label
    for m in SUBSTITUTION.findall(text):
        inner = m[0] or m[1]
        if not inner:
            continue
        inner_low = normalize(inner).lower()
        for pattern, label in DANGEROUS:
            if re.search(pattern, inner_low):
                return f"{label} (inside a command substitution)"
    return None


def check_protected(path):
    norm = os.path.normpath(normalize(path)).replace("\\", "/").lower()
    # best-effort symlink resolution for existing paths; a path that resolves
    # through a symlink on the protected list is protected too.
    der = path
    try:
        if os.path.islink(path) or os.path.exists(path):
            der = os.path.realpath(path)
    except OSError:
        pass
    der = os.path.normpath(normalize(der)).replace("\\", "/").lower()
    for pattern, label in PROTECTED_PATHS:
        if re.search(pattern, norm) or re.search(pattern, der):
            return label
    return None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "bash"
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("payload is not an object")
    except Exception as err:
        if mode == "protect":
            # fail closed: unknown write target ~= assume dangerous
            deny(f"Guard could not parse the write request ({err.__class__.__name__}); "
                 "denying in protect mode. Repeat the edit if it is legitimate.")
        print("guard: invalid payload (allowed, bash mode fail-open)", file=sys.stderr)
        sys.exit(0)

    if mode == "bash":
        text = get_command(payload)
        if not text:
            sys.exit(0)  # nothing we recognize — passthrough (documented limitation)
        label = check_dangerous(text)
        if label:
            deny(f"Guard blocked: {label}. "
                 "This pattern is on the destructive-command blocklist. "
                 "If it is intentional, ask the human to run it outside the agent.")
    elif mode == "protect":
        path = get_path(payload)
        if not path:
            deny("Guard could not determine the file path of this write "
                 "(protect mode fails closed on unknown targets).")
        label = check_protected(path)
        if label:
            deny(f"Guard blocked: {path} matches {label}. "
                 "Get explicit human confirmation before modifying this file.")
    else:
        print(f"guard: unknown mode '{mode}' (allowed)", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
