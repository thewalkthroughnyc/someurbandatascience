PY = python3

pull:        ## 01 — band, tracts, ACS rent, Gate 1
	$(PY) src/01_pull_acs.py

walktimes:   ## 02 — OSMnx network walk times (slow first run)
	$(PY) src/02_walk_times.py

clean_join:  ## 03 — clean + scatter, Gate 2
	$(PY) src/03_clean_join.py

model:       ## 04 — fit the M model, export coefficients.json for the p5 tool
	$(PY) src/04_model.py

all: pull walktimes clean_join model

test:
	$(PY) tests/test_lib.py

.PHONY: pull walktimes clean_join model all test
