PYTHON ?= python3
PYTHONPATH := src
export PYTHONPATH

.PHONY: check test validate smoke executable-smoke release-check clean

check: test validate release-check
	$(PYTHON) scripts/validate_paper_artifact.py

test:
	$(PYTHON) -m unittest discover -s tests -v

validate:
	$(PYTHON) -m tubebench.cli validate
	$(PYTHON) -m tubebench.cli validate-longform
	$(PYTHON) -m tubebench.cli validate-executable
	$(PYTHON) -m tubebench.cli validate-live-youtube
	$(PYTHON) -m tubebench.cli validate-live-public-video

smoke:
	rm -rf runs/smoke
	$(PYTHON) -m tubebench.cli run --agent mock-perfect --seed 1 --output runs/smoke
	$(PYTHON) -m tubebench.cli summarize runs/smoke/results.jsonl

executable-smoke:
	rm -rf runs/executable-smoke
	$(PYTHON) -m tubebench.cli run-executable \
		--agent scripted \
		--seed 1 \
		--output runs/executable-smoke/scripted
	$(PYTHON) -m tubebench.cli run-executable \
		--agent noop \
		--seed 1 \
		--output runs/executable-smoke/noop

release-check:
	$(PYTHON) scripts/release_check.py

clean:
	rm -rf runs build dist
