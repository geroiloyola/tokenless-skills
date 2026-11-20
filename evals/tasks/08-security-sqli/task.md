# 08-security-sqli

## Prompt
app.py interpolates user input into SQL. Fix the injection (parameterized query), keep find_user's signature and return type, add a test proving the payload "x' OR '1'='1" returns no rows unless they exist.

## Verification
`verify.sh` (exit 0 = pass). Contract: evals/PREREGISTRATION.md
