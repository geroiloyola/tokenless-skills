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

Para instalar en otro proyecto, ejecuta `/ruta/a/tokenless-skills/install.sh project`
desde la raíz de ese proyecto.

## Skills

| Skill | Uso | body tok |
|-------|-----|---------:|
| repo-context | AGENTS.md verificado con comandos y patrones | 466 |
| spec-brainstorm | Petición vaga → spec con criterios observables | 441 |
| write-plan | Spec → tareas de 10–30 min con archivos exactos | 431 |
| implement-tdd | RED → GREEN → REFACTOR por unidad de trabajo | 580 |
| systematic-debugging | Causa raíz vía hipótesis falsables | 411 |
| verify-done | Gates (typecheck/lint/tests/build) + revisión del diff | 510 |
| remember-correction | Corrección del usuario → regla de 1 línea | 398 |
| learn-instinct | Patrones con confianza (0.2–0.9) que se podan | 411 |
| subagent-execute | 1 tarea = 1 worktree = 1 subagente | 526 |
| fresh-review | Review bloqueante en contexto limpio, no sesgado | 453 |
| webapp-testing | Browser real: consola, red, a11y | 371 |
| security-review | Secretos, inyección, authz sobre el diff | 509 |
| design-review | Dirección estética + token set + auditoría | 596 |
| eval-harness | Re-ejecutar 5 tareas fijas en cada cambio del kit | 341 |

Body total: 6444 tokens; descripciones: 653 tokens
(`o200k_base`, `python3 scripts/measure_tokens.py`).

## Flujo

`spec-brainstorm → write-plan → implement-tdd → fresh-review → verify-done`,
con `subagent-execute` como runner paralelo y los dos skills de memoria
(`remember-correction`, `learn-instinct`) acumulando reglas entre sesiones.

## Presupuesto

CI valida frontmatter y exige desc ≤55 / body ≤600 tokens con `o200k_base`.

```bash
python3 -m pip install -r scripts/requirements.txt
python3 scripts/measure_tokens.py
python3 -m unittest discover -s tests -v
python3 scripts/bench.py --dry-run
```

### Evaluación de comportamiento

`python3 scripts/bench.py --adapter /ruta/al/adapter` ejecuta las cinco tareas
fijas con y sin el kit en directorios nuevos. Usa un adaptador a un host que
descubra `.agents/skills`; debe iniciar una sesión nueva por llamada, leer el
prompt de stdin, trabajar en el directorio actual y usar el mismo modelo y
configuración en ambas variantes, sin skills globales del kit. Devuelve JSON
por stdout con `tokens` (uso total reportado por el host) y `activated_skills`
(nombres observados en la traza). Si el host no expone un dato, omítelo: se
registra `null`. Los verificadores miden el resultado por separado. El
`--dry-run` de CI prueba que cada criterio rechaza el estado inicial y acepta
la solución de referencia; no llama a modelos ni mide activación o consumo.

Hosts: Claude Code, Codex, OpenCode, Gemini CLI, Cursor, y cualquier host Agent Skills 1.0.
License: MIT.
