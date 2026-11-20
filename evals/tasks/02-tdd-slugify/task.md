# 02-tdd-slugify

## Prompt
extend slugify in slug.py: strip accents (unicodedata), drop punctuation completely, collapse runs of separators into single hyphens, lowercase; probes it must satisfy: "Héllo, World!" -> hello-world ; "  A  B  " -> a-b ; "Ça_va?" -> ca-va. Add tests first.

## Verification
`verify.sh` (exit 0 = pass). Contract: evals/PREREGISTRATION.md
