# tokenless-skills — developer entry points (optional; tests run without make)
.PHONY: test check

test:
	python3 tests/run_all.py

check:
	python3 scripts/check_skills.py --strict
	bash -n install.sh
