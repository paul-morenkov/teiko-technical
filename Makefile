PYTHON := python3
VENV   := .venv
PY     := $(VENV)/bin/python

.PHONY: setup pipeline dashboard

setup:
	$(PYTHON) -c "import sys; assert sys.version_info >= (3, 12), f'Python 3.12+ required, found {sys.version}'"
	$(PYTHON) -m venv --without-pip $(VENV)
	$(PY) -m ensurepip --upgrade
	$(PY) -m pip install -e .

pipeline:
	$(PY) load_data.py
	$(PY) analyze_data.py

dashboard:
	$(VENV)/bin/streamlit run dashboard.py --server.port 8501
