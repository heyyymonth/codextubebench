PYTHON ?= python3
PYTHONPATH := src
export PYTHONPATH

.PHONY: test validate smoke release-check clean

test:
	$(PYTHON) -m unittest discover -s tests -v

validate:
	$(PYTHON) -m tubebench.cli validate

smoke:
	rm -rf runs/smoke
	$(PYTHON) -m tubebench.cli run --agent mock-perfect --seed 1 --output runs/smoke
	$(PYTHON) -m tubebench.cli summarize runs/smoke/results.jsonl

release-check:
	$(PYTHON) scripts/release_check.py

clean:
	rm -rf runs build dist
