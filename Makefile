.PHONY: static_analysis test

PYTHONPATH=$(abspath ./src)

static_analysis:
	flake8

test: static_analysis
	PYTHONPATH=$(PYTHONPATH) python3 -m unittest discover -p '*_test.py' -s tests
