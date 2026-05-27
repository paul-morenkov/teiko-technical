.PHONY: setup pipeline dashboard

setup:
	pip install -e .

pipeline:
	python load_data.py
	python analyze_data.py

dashboard:
	streamlit run dashboard.py
