.PHONY: test

PYTHONPATH=$(abspath ./src)

test:
	PYTHONPATH=$(PYTHONPATH) python -m unittest discover -p '*_test.py' -s tests
