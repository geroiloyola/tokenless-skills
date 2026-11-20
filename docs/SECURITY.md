# Security model

## What the guard is — and is not

`extras/vibe/guard.py` is a **best-effort accident guard** built on pattern matching. It is **not a sandbox, not an OS-level security boundary, and not complete shell security**. Its purpose is to stop the common destructive mistakes of an autonomous coding agent *by accident*, and to route the uncommon ones to a human.

This is a hard scope statement, not modesty. A regex filter can be bypassed by construction; we enumerate known ones below and keep them as regression tests rather than pretending otherwise.

## What it protects

Protect mode (`pre_tool` on file-write tools) denies writes to:

- `.env` and `.env.<anything>` files (any case, nested paths, traversal)
- `secrets.env` / `secret.env` / `secrets.key` (any case)
- anything inside `.git/` or `.ssh/`
- SSH private keys (`id_rsa`, `id_dsa`, `id_ecdsa`, `id_ed25519`, any case)
- `.netrc`, `.npmrc`, `.pypirc`
- AWS credentials (anything under `.aws/`), Kubernetes config (`.kube/config`), Docker registry auth (`.docker/config.json`), GPG keyrings (`.gnupg/`)
- package-manager lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, poetry/cargo/uv lock, `go.sum`)
- paths that resolve through a symlink into any of the above (best-effort; resolved only when the target file already exists)

Bash mode (`pre_tool` on shell tools) denies common catastrophic commands: `rm -rf` of `/` (and `/*`), `~`/`~user`/`~/`, `$HOME`/`${HOME}`/`$HOME/`, `.git`, `.`/`..`, or a wildcard/current-directory target; depth-1 system dirs (`rm -rf /home`, `/etc`, `/usr`, …); Git Bash drive-mount roots (`rm -rf /c/`); Windows drive roots (`rm -rf C:/`) and `C:/Users`/`C:/Windows`; anything with `--no-preserve-root`; `find -delete` against `/`, `~`, or the current tree when no narrowing `-name`/`-regex` predicate is present (depth-2+ paths like `rm -rf /tmp/build` and `rm -rf ~/.cache/pip` stay legal); `mkfs`; `dd`/`shred` to block devices (except `/dev/null`); fork bombs; `chmod 777` with any flag arrangement or none; force pushes (`--force`, `-f`, `-ff`, `+refspec`, and `--force-with-lease=false`); `git reset --hard origin…`; `git clean`; `git checkout -- .`; piping remote content to any shell, python, node, deno, bun, perl, or ruby (any shell variant, including via `zsh`); `bash <(curl …)`; `eval "$(wget …)"`; `npm publish`/`twine upload`/`cargo publish` (except npm `--dry-run`); `DROP DATABASE/TABLE`; `TRUNCATE TABLE`; raw disk redirects. Command-substitution bodies (`$(…)`, backticks) are extracted and re-scanned.

Protect mode (`pre_tool` on write/edit tools) denies writes to: `.env[*]`, `secret(.s).[env|key]`, `.git/`, `.ssh/`, SSH private keys (any case), `.netrc`/`.npmrc`/`.pypirc`, AWS credentials (`.aws/`), Kubernetes config (`.kube/config`), Docker registry auth (`.docker/config.json`), GPG keyrings (`.gnupg/`), and lockfiles.

## Failure behavior

- **Bash mode fails open.** If the payload is unparseable or unrecognized, the command proceeds (the guard is an accident guard; blocking every unrecognized command would break agents). A warning goes to stderr.
- **Protect mode fails closed.** If the guard cannot determine what file is being written, it denies and explains that the write can be repeated once legitimate. Unknown targets ≈ blocked targets.

## What it cannot detect (the honest list)

Verified-bypass shapes that remain possible by design of a regex filter; each is documented here rather than hidden:

- commands assembled so no static substring matches (computed targets, base64/unicode obfuscation, `IFS` tricks, variable indirection beyond the literal `$HOME`/`${HOME}` spellings)
- destructive operations run through interpreters (`python -c`, `perl -e`, `node -e`) — the guard blocks *piping remote content* to them, not local interpreter misuse
- `rm -rf` of an **existing directory argument** the guard cannot classify: depth-2+ absolute paths (`rm -rf /home/u/proj/dist` is legal by design), or a depth-1 dir outside the known-system list (`rm -rf /somedata/`)
- deeper home/user-path forms: `rm -rf ~/sub/x`, `rm -rf $HOME/sub/x`, `rm -rf ~user/sub` (only bare `~`, `~user`, `~/`, `$HOME`, `$HOME/` are caught)
- relative traversal with a named component: `rm -rf ../sibling` (bare `..`, `.` forms are caught)
- destructive effects via legitimate tools (`mv`, `cp` over, build tooling pointed at the wrong directory)
- anything after the first tool call the guard does not scan (e.g. tools beyond `bash`/`write_file`/`edit`); unknown hook modes fail open (stderr note)
- secrets exfiltrated through *network reads*, which the guard does not police at all — it inspects local destructive patterns only

## Required layers still (guard ≠ permissions)

1. **OS permissions/run-as** — the agent's user must not own what the agent must not destroy.
2. **Sandboxing** (containers on CI/CD, host approval modes) — the actual security boundary.
3. **Git** — commits before risky operations make almost every destructive accident recoverable.
4. **The guard** — cheap tripwire for the accident case. Nothing more.

## Non-goals

- No daemon, no logging service, no telemetry. Denial reasons contain the pattern label and the path, never file contents.
- No automatic updates: `install.sh` never phones home. The only network operation in the whole kit is `webapp-testing`'s optional axe-core CDN fetch (documented in that skill) — pin or vendor it if that matters to your threat model.

## Reporting

See `SECURITY.md` for responsible disclosure.
