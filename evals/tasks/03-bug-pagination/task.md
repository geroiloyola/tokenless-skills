# 03-bug-pagination

## Prompt
user report: "page 1 shows the second block of rows". Tests currently pass but encode the bug. Fix the root cause and repair the tests to encode correct 1-based pagination.

## Verification
`verify.sh` (exit 0 = pass). Contract: evals/PREREGISTRATION.md
