# 05-refactor-extract

## Prompt
refactor invoice.py: extract the per-line arithmetic (gross minus discount floored at zero) into line_subtotal(line) and use it in both passes; calculate_total and all public behavior must stay identical (assert in preview pass still holds).

## Verification
`verify.sh` (exit 0 = pass). Contract: evals/PREREGISTRATION.md
