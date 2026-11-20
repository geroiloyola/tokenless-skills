# BASELINE.md — Linea base de tokens y calidad (Fase 0)

Estado del analisis: solo lectura. Ningun skill fue modificado.

## Metodo de medicion

- Tokenizer real: `tiktoken` encoding `o200k_base` (era GPT-4o). Se eligio como
  representante medible; los hosts soportados usan tokenizers distintos
  (Claude, Gemini), por lo que los numeros deben leerse como aproximaciones
  dentro de un margen de unos pocos puntos porcentuales, no como cifras
  exactas para cada host.
- Reproducir con:

  ```
  pip install tiktoken        # dependencia solo de desarrollo, no de runtime
  python3 scripts/measure_tokens.py --json evals/results/tokens-baseline.json
  ```

- Sin tiktoken, el script degrada al estimador chars/4, rotula la salida como
  `UNMEASURED` y sale con codigo 2, para que CI distinga estimacion de
  medicion.
- El estimador chars/4 que usaba el README fue validado contra el tokenizer:
  error absoluto medio 12.2 tokens por skill (2.6% de la media); por skill el
  error va de -3.5% a +5.6%. Suficiente como fallback, insuficiente como cifra
  publicitaria.
- Fecha de medicion: la de este commit, sobre el arbol de trabajo limpio.

## Resultado por skill (medido, o200k_base)

| skill                | cuerpo (tokens) | descrip. | est4 cuerpo | err% | lineas |
|----------------------|----------------:|---------:|------------:|-----:|-------:|
| design-review        |             572 |       44 |         582 |  1.7 |     45 |
| eval-harness         |             373 |       50 |         360 | -3.5 |     37 |
| fresh-review         |             481 |       43 |         504 |  4.8 |     35 |
| implement-tdd        |             557 |       39 |         567 |  1.8 |     46 |
| learn-instinct       |             408 |       47 |         395 | -3.2 |     34 |
| remember-correction  |             369 |       41 |         386 |  4.6 |     35 |
| repo-context         |             482 |       37 |         472 | -2.1 |     58 |
| security-review      |             523 |       46 |         530 |  1.3 |     33 |
| spec-brainstorm      |             457 |       42 |         478 |  4.6 |     46 |
| subagent-execute     |             542 |       53 |         547 |  0.9 |     44 |
| systematic-debugging |             426 |       37 |         450 |  5.6 |     32 |
| verify-done          |             454 |       38 |         452 | -0.4 |     51 |
| webapp-testing       |             412 |       42 |         416 |  1.0 |     34 |
| write-plan           |             440 |       41 |         428 | -2.7 |     48 |
| **total**            |         **6496** | **600**  |             |      |        |

- Cuerpo: min 369 / mediana 457 / media 464 / max 572 tokens.
- Coste de contexto siempre cargado (14 descripciones): **600 tokens medidos**.
- Coste por activacion tipica: descripcion + cuerpo ~= 500 tokens (medido,
  mediana 43 + 457).
- Todas las descripciones estan bajo el presupuesto de 40 tokens? No: 11 de 14
  miden 41-53 tokens. Correccion requerida en Fase 1 para llegar a Plata.
- El JSON crudo versionado vive en `evals/results/tokens-baseline.json`.

## Reconciliacion con figuras previas del README

| Afirmacion previa | Estado basado en esta medicion |
|---|---|
| "~500 tokens por skill" | Medido: media 464 cuerpo + 43 descrip. Correcta. |
| "360-581 tokens por skill" | Era chars/4. Real: 369-572. Reescribir con cifras medidas. |
| "718 always-loaded" | Era estimacion. Medido: 600. Reescribir. |
| "worst-case total 7,285" |Hipotesis sin comando reproducible en el repo. Marcar como hipotesis o eliminar. |
| "90% capability retention" | Hipotesis. Sin arnes de evals es inverificable. Se elimina o se etiqueta. |
| "% vs ECC / otros" | Hipotesis. Solo se podra afirmar tras Fase 2 (A/B/C con >=5 repeticiones). |

## Solapamientos entre skills

1. **implement-tdd <-> verify-done**: ambos exigen "build + lint + typecheck +
   tests antes de commit/push" (implement-tdd regla 7 y pasos 5-6; verify-done
   gates 1-5). Duplicacion de logica de gating con orden redistribuible; en
   repos sin AGENTS.md, cada uno puede inventar comandos distintos.
2. **fresh-review <-> verify-done**: la descripcion de fresh-review exige
   "after implement-tdd, before verify-done", pero el reporte de cierre de
   implement-tdd solo menciona a verify-done. fresh-review puede quedarse
   sin disparar en la cadena; y ambos leen el diff completo.
3. **learn-instinct <-> remember-correction**: escriben en
   `~/.agents/memory/` con formatos de una linea distintos y barras de
   calidad casi duplicadas (instincts: rechazar lo no falsable; lessons:
   rechazar "be more careful"). Riesgo de colision de formatos en el mismo
   archivo si un host los mezcla.
4. **eval-harness <-> (futuro) arnes evals/**: la misma responsabilidad
   (medir antes/despues) con estudiantes distintos (`prompts/eval/` vs el
   arnes de este repo). En Fase 2 hay que fusionar, no duplicar.
5. **spec-brainstorm <-> write-plan**: secuenciacion correcta y explicita
   ("Wait for explicit yes" / "Do not implement here"), pero la descripcion
   de write-plan ("Use after spec-brainstorm") puede re-disparar
   spec-brainstorm cuando ya existe spec. Falta anti-disparador.
6. **design-review -> webapp-testing**: dependencia cruzada declarada dentro
   del cuerpo y verificable en el kit, Correcta, pero `webapp-testing` debe
   estar instalada o el paso de auditoria se degrada sin decirlo.

## Instrucciones ambiguas

- `design-review`: "The searchable catalog lives in the upstream skill if
  installed" no dice que skill ni como detectarla. Ilegible por terceros.
- `eval-harness`: pide registrar "tokens" por tarea pero no define como
  obtenerlos en cada host (`vibe --prompt`, `claude -p`, ...). campos
  no medibles hoy en sesiones headless sin salida JSON del host.
- `write-plan`: `Est:` se llena "based on similar tasks or user input"
  sin criterio; instrucciones de estimacion no verificables.
- `subagent-execute`: "run verify-done-style gates" sin definir el orden ni
  que se delega; una implementacion podria ejecutar gates fuera de orden.
- `learn-instinct`: `expires: <date>` sin formato ni zona horaria.
- `remember-correction`: `priority:HIGH|MEDIUM|LOW` sin criterio de eleccion.

## Pasos sin criterio de parada

- `systematic-debugging`: ciclo de hipotesis sin tope; si N hipotesis mueren,
  no hay escala a humano (implement-tdd tiene el tope de 2 intentos, pero
  debugging invocado directo no hereda ese guard).
- `repo-context`: modo update no define tope: puede proponer cambios
  ilimitados de secciones antes de pedir aprovacion.
- `learn-instinct`: promocion a AGENTS.md pide permiso (bien), pero la poda
  no dice que hacer cuando el archivo nunca baja de 40 lineas con todo >=0.7.

## Los 10 mayores riesgos de calidad (priorizados)

1. Gating duplicado implement-tdd/verify-dev... errata: verify-done; en repos sin
   AGENTS.md, comandos inventados y orden inconsistente. (Solapamiento 1)
2. fresh-review puede no disparar nunca: nadie de la cadena lo nombra y su
   requisito se declara solo en su propia descripcion. (Solapamiento 2)
3. `~/.agents/memory/lessons.md` e `instincts.md`: mismo directorio, formatos
   distintos, barras de calidad duplicadas. (Solapamiento 3)
4. eval-harness referencia `prompts/task-templates.md` "in the kit repo"
   (opcional) y metrica "tokens" sin procedimiento de medicion por host.
5. Descripciones sin anti-disparador ("no usar para...") en las 14 skills;
   exceso de activaciones (sobre-trigger). Medicion: 0/14 tienen anti-trigger.
6. 11/14 descripciones exceden el presupuesto de 40 tokens (41-53). Fase 1.
7. design-review depende de un "upstream skill" externo indefinido.
8. systematic-debugging sin tope de hipotesis ni escalado.
9. Sin CI: los cambios pueden crecer tokens o romper contratos sin
   deteccion (se ataca en Fase 2 con gate de tokens/exito).
10. Cifras del README no reproducibles con comando versionado (se resuelve
    con measure_tokens.py + este documento; actualizar README en Fase 6).

## Que NO se verifico en Fase 0

- Tasa de activacion real (precision/recall de disparo): requiere Fase 2.
- Calidad A/B frente a skills verbosas o frente a alternativas (ECC,
  Superpowers):requiere Fase 2.
- Compatibilidad de ejecucion de los skills en cada host (solo estatica en
  docs/HOSTS.md).
- Como tokenizan exactamente Claude/Gemini: tiktoken o200k_base es
  representativo, no identico a cada host.
