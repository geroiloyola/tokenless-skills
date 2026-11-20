# 04-bug-cache

## Prompt
bug report: after invalidate('user','a'), by_kind('user') still yields the entry for 'a'. Fix the root cause; add a regression test.

## Verification
`verify.sh` (exit 0 = pass). Contract: evals/PREREGISTRATION.md
