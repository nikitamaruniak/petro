.PHONY: test

PYTHONPATH=$(abspath ./src)

test:
	PYTHONPATH=$(PYTHONPATH) python3 -m unittest discover -p '*_test.py' -s tests
