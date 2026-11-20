# tokenless-skills — developer entry points (optional; tests run without make)
.PHONY: test check bench-prep bench-dry bench

test:
	python3 tests/run_all.py

check:
	python3 scripts/check_skills.py --strict
	bash -n install.sh

# benchmark (misleadingly named scripts/bench.py runs the preregistered
# A/B/D matrix from evals/PREREGISTRATION.md; run fetching first)
bench-prep:
	python3 evals/fetch_competitors.py

bench-dry:
	python3 scripts/bench.py --dry-run

bench:
	python3 evals/fetch_competitors.py --skip-existing
	python3 scripts/bench.py
