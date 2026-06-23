PYTHON ?= python
PIP ?= pip
STREAMLIT ?= streamlit

.PHONY: install install-dev test lint run

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

install-dev:
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

test:
	pytest

lint:
	ruff check .

run:
	$(PYTHON) -m streamlit run ui/streamlit_app.py
