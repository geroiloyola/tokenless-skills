#!/usr/bin/env python3
"""QA hook para Mistral Vibe CLI — post_tool tras cada edición de archivo.

Corre typecheck y lint del proyecto y, si fallan, inyecta los errores como
`hook_specific_output.additional_context` para que el agente los vea en el
acto (coste de contexto: cero cuando todo está verde).

Config por repo en .agents/qa.json (opcional):
  {"typecheck": "npx tsc --noEmit", "lint": "npx eslint --quiet <files>",
   "timeout": 60, "extensions": [".ts", ".tsx", ".js", ".jsx"]}

Si no hay qa.json, detecta por archivos del cwd:
  tsconfig.json      -> npx tsc --noEmit
  pyproject/ruff.toml-> ruff check <file>
  cargo              -> cargo check -q
  go.mod             -> go vet ./...
Fallback: nada (passthrough).

Uso: hooks.toml -> command = "python3 <kit>/scripts/qa.py"
Exit siempre 0; un fallo del hook nunca bloquea la edición.
"""
import json
import os
import re
import subprocess
import sys

MAX_CHARS = 1800  # recorte para no inflar el contexto
CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rs", ".vue", ".svelte", ".astro"}
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")


def run(cmd, timeout, cwd):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"timeout tras {timeout}s: {cmd}"
    except Exception as e:  # noqa: BLE001
        return 1, f"hook error: {e}"


def tool_available(cmd, root):
    """Evita falsos positivos: nunca deja que npx descargue un paquete homónimo.

    - `npx <tool>` solo se acepta si el binario existe en node_modules/.bin.
    - `npm run <script>` solo si el script existe en package.json.
    - Cualquier otro comando: debe existir en PATH.
    """
    parts = cmd.split()
    if not parts:
        return False
    if parts[0] == "npx":
        i = 1
        while i < len(parts) and parts[i].startswith("-"):
            i += 1
        if i >= len(parts):
            return False
        tool = parts[i]
        return os.path.isfile(os.path.join(root, "node_modules", ".bin", tool))
    if parts[0] == "npm" and len(parts) > 1 and parts[1] == "run":
        pkg = os.path.join(root, "package.json")
        if not os.path.isfile(pkg) or len(parts) < 3:
            return False
        try:
            data = json.load(open(pkg))
            return parts[2] in (data.get("scripts") or {})
        except Exception:
            return False
    from shutil import which

    return which(parts[0]) is not None


def detect(root):
    cfg = os.path.join(root, ".agents", "qa.json")
    if os.path.isfile(cfg):
        try:
            return json.load(open(cfg))
        except Exception:
            pass
    if os.path.isfile(os.path.join(root, "tsconfig.json")):
        return {"typecheck": "npx tsc --noEmit", "timeout": 60}
    if os.path.isfile(os.path.join(root, "ruff.toml")) or os.path.isfile(os.path.join(root, "pyproject.toml")):
        return {"typecheck": "", "lint": "ruff check {file}", "timeout": 30}
    if os.path.isfile(os.path.join(root, "go.mod")):
        return {"typecheck": "go vet ./...", "timeout": 60}
    if os.path.isfile(os.path.join(root, "Cargo.toml")):
        return {"typecheck": "cargo check -q", "timeout": 90}
    return {}


def trim(text):
    text = ANSI.sub("", text).strip()
    if len(text) <= MAX_CHARS:
        return text
    return text[:MAX_CHARS] + f"\n… (recortado, {len(text)} chars en total)"


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = payload.get("tool_input") or {}
    path = ti.get("path") or ti.get("file_path") or ti.get("filename") or ""
    if not path or os.path.splitext(path)[1] not in CODE_EXT:
        sys.exit(0)
    if not os.path.isfile(path):
        sys.exit(0)

    root = payload.get("cwd") or os.getcwd()
    cfg = detect(root)
    if not cfg:
        sys.exit(0)
    timeout = int(cfg.get("timeout", 60))

    problems = []
    checks = []
    for key in ("typecheck", "lint"):
        cmd = (cfg.get(key) or "").strip()
        if not cmd:
            continue
        cmd = cmd.replace("{file}", path)
        if not tool_available(cmd, root):
            continue
        code, out = run(cmd, timeout, root)
        checks.append(key)
        if code != 0:
            problems.append(f"[{key}] `{cmd}` (exit {code}):\n{trim(out)}")

    if not problems:
        sys.exit(0)

    msg = (
        "QA hook: tu edición dejó el repo en rojo. Corrige esto antes de seguir "
        "(no lo ignores ni lo pospongas):\n\n" + "\n\n".join(problems)
    )
    print(json.dumps({
        "hook_specific_output": {"additional_context": trim(msg)},
        "system_message": f"QA: {', '.join(checks)} con errores en {os.path.basename(path)}",
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
