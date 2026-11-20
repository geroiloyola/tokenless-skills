#!/usr/bin/env python3
"""Guard de seguridad para hooks de Mistral Vibe CLI (hooks.toml).

Modos:
  bash     -> pre_tool hook para `bash`/`process_start`: bloquea comandos destructivos.
  protect  -> pre_tool hook para write_file/edit: protege archivos sensibles.

Contrato Vibe hooks: payload JSON en stdin; respuesta JSON en stdout.
  exit 0 + {"decision":"deny","reason":"..."}  -> bloquea
  exit 0 + stdout vacío                        -> permite (passthrough)
"""
import json
import re
import sys

# --- patrones de comandos destructivos (regex, case-insensitive) ---
DANGEROUS = [
    (r"\brm\s+(-[a-z]*[rf][a-z]*\s+)+/(\s|$)", "borrado recursivo de la raíz"),
    (r"\brm\s+(-[a-z]*[rf][a-z]*\s+)+(~|\$HOME)(\s|$)", "borrado recursivo del home"),
    (r"\brm\s+(-[a-z]*[rf][a-z]*\s+)+\.git\b", "borrado del directorio .git"),
    (r"\bgit\s+push\b[^\n]*(--force|-f)(\s|$)(?!.*--force-with-lease)", "git push --force sin lease"),
    (r"\bgit\s+reset\s+--hard\b[^\n]*\borigin", "reset --hard contra origin"),
    (r"\bgit\s+clean\s+-[a-z]*[xdf]", "git clean destructivo"),
    (r"\bgit\s+checkout\s+--\s+\.", "descarta todos los cambios locales"),
    (r"\b(mkfs|dd\s+if=.*of=/dev/)", "escritura a dispositivo de bloque"),
    (r":\(\)\s*\{\s*:\|\s*:\s*&\s*\}\s*;", "fork bomb"),
    (r"\bchmod\s+-R\s+777\b", "chmod 777 recursivo"),
    (r"\b(curl|wget)\b[^\n]*\|\s*(bash|sh)\b", "pipe remoto a shell"),
    (r"\bnpm\s+publish\b|\btwine\s+upload\b|\bcargo\s+publish\b", "publicación de paquete"),
    (r"\bdrop\s+(database|table)\b", "DROP de base de datos"),
    (r"\btruncate\s+table\b", "TRUNCATE de tabla"),
    (r">\s*/dev/sd[a-z]", "escritura a disco crudo"),
]

# --- archivos que un agente no debe sobrescribir sin humano ---
PROTECTED_PATHS = [
    (r"(^|/)\.env(\.[\w.-]+)?$", "archivo .env (secretos)"),
    (r"(^|/)\.git/", "interior de .git"),
    (r"(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock|Cargo\.lock|uv\.lock|go\.sum)$", "lockfile (regenerar con el gestor, no editar a mano)"),
    (r"(^|/)(id_rsa|id_ed25519|\.netrc|\.npmrc|\.pypirc)$", "credenciales"),
]


def respond(decision=None, reason=None, system_message=None):
    out = {}
    if decision:
        out["decision"] = decision
    if reason:
        out["reason"] = reason
    if system_message:
        out["system_message"] = system_message
    print(json.dumps(out))
    sys.exit(0)


def get_command(payload):
    ti = payload.get("tool_input") or {}
    if isinstance(ti, str):
        return ti
    for key in ("command", "cmd", "script"):
        if isinstance(ti.get(key), str):
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


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "bash"
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # payload ilegible: no bloquear, pero avisar en stderr
        print("guard: payload inválido", file=sys.stderr)
        sys.exit(0)

    text = get_command(payload) if mode == "bash" else get_path(payload)
    if not text:
        sys.exit(0)

    if mode == "bash":
        low = text.lower()
        for pattern, label in DANGEROUS:
            if re.search(pattern, low):
                respond(
                    decision="deny",
                    reason=(
                        f"Bloqueado por guard: {label}. "
                        "Si es intencional, pídelo explícitamente al humano y "
                        "ejecútalo tú fuera del agente."
                    ),
                )
    elif mode == "protect":
        norm = text.replace("\\", "/")
        for pattern, label in PROTECTED_PATHS:
            if re.search(pattern, norm):
                respond(
                    decision="deny",
                    reason=(
                        f"Bloqueado por guard: {label}. "
                        "Pide confirmación al humano antes de modificar este archivo."
                    ),
                )
    sys.exit(0)


if __name__ == "__main__":
    main()
