# tokenless-skills

14 skills compactos de alta densidad para agentes (Agent Skills 1.0): flujo completo
spec → plan → TDD → review → verificación, con coste de contexto mínimo. Cada skill
cumple un presupuesto verificado por CI: descripción ≤55 tokens, cuerpo ≤600.

## Install

```bash
git clone --depth 1 https://github.com/geroiloyola/tokenless-skills.git
cd tokenless-skills && ./install.sh            # claude + codex detectados + .agents/skills
./install.sh claude codex                      # hosts explícitos
./install.sh project                           # solo ./.agents/skills (commiteable)
```

## Skills

| Skill | Uso | body tok |
|-------|-----|---------:|
| repo-context | AGENTS.md verificado con comandos y patrones | 466 |
| spec-brainstorm | Petición vaga → spec con criterios observables | 441 |
| write-plan | Spec → tareas de 10–30 min con archivos exactos | 431 |
| implement-tdd | RED → GREEN → REFACTOR por unidad de trabajo | 580 |
| systematic-debugging | Causa raíz vía hipótesis falsables | 411 |
| verify-done | Gates (typecheck/lint/tests/build) + revisión del diff | 466 |
| remember-correction | Corrección del usuario → regla de 1 línea | 398 |
| learn-instinct | Patrones con confianza (0.2–0.9) que se podan | 411 |
| subagent-execute | 1 tarea = 1 worktree = 1 subagente | 526 |
| fresh-review | Review bloqueante en contexto limpio, no sesgado | 467 |
| webapp-testing | Browser real: consola, red, a11y | 393 |
| security-review | Secretos, inyección, authz sobre el diff | 509 |
| design-review | Dirección estética + token set + auditoría | 596 |
| eval-harness | Re-ejecutar 5 tareas fijas en cada cambio del kit | 358 |

Body total: 6453 tokens (o200k_base, `python3 scripts/measure_tokens.py`);
coste always-loaded (descripciones): ~660 tokens.

## Flujo

`spec-brainstorm → write-plan → implement-tdd → fresh-review → verify-done`,
con `subagent-execute` como runner paralelo y los dos skills de memoria
(`remember-correction`, `learn-instinct`) acumulando reglas entre sesiones.

## Presupuesto

CI falla si un skill supera desc ≤55 / body ≤600 tokens (`scripts/measure_tokens.py`).
Hosts: Claude Code, Codex, OpenCode, Gemini CLI, Cursor, y cualquier host Agent Skills 1.0.
License: MIT.
