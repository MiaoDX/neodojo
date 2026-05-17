.PHONY: test demo-html

PYTHON ?= python3

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests

demo-html:
	PYTHONPATH=src $(PYTHON) -m neodojo demo-html --out outputs/html-demo
