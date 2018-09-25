.PHONY: test static_analysis unit_tests acceptance_tests

PYTHONPATH=$(abspath ./src)

test: static_analysis unit_tests acceptance_tests

static_analysis:
	@echo "\n* Running static code analysis...\n"
	flake8

unit_tests:
	@echo "\n* Running unit tests...\n"
	PYTHONPATH=$(PYTHONPATH) python3 -m unittest discover -p '*_test.py' -s tests

acceptance_tests:
	@echo "\n* Running acceptance tests...\n"
	PYTHONPATH=$(PYTHONPATH) cd acceptance_tests && ./run_tests.sh
