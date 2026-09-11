.PHONY: setup test build serve all clean

VENV := .venv
PY := $(VENV)/bin/python

setup:
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -e ".[dev]"

test:
	$(PY) -m pytest -q

build:
	$(PY) -m bedford_corridor.build_json

serve:
	cd web && ../$(PY) -m http.server 8000

all: setup build
	@echo ""
	@echo "Build complete. web/data/corridor.json is up to date."
	@echo "Run 'make test' to see the suite — 11 failures are EXPECTED right now,"
	@echo "one per stubbed function in segmentation.py, denominator.py, stats/did.py,"
	@echo "and stats/interval.py. Everything else should pass."
	@echo "Run 'make serve' and open http://localhost:8000 to view the site."

clean:
	rm -rf $(VENV) data_cache web/data/corridor.json
