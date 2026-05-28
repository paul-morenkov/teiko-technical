UV   := $(shell command -v uv 2>/dev/null || echo $(HOME)/.local/bin/uv)
VENV := .venv
PY   := $(VENV)/bin/python

.PHONY: setup pipeline dashboard

setup:
	@command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
	$(UV) python install 3.12
	$(UV) sync

pipeline:
	$(PY) load_data.py
	$(PY) analyze_data.py

dashboard:
	$(VENV)/bin/streamlit run dashboard.py --server.port 8501
