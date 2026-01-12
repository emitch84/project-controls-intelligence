.PHONY: setup generate_data build_db run_checks run_app test clean

setup:
	pip install -r requirements.txt

generate_data:
	python -m src.data_gen.generate_data

build_db:
	python -m src.etl.load_all

run_checks:
	python -m src.quality.run_checks

run_app:
	streamlit run src/app/streamlit_app.py

test:
	pytest tests/

clean:
	rm -rf data/raw/*.csv
	rm -rf data/processed/*.db
	rm -rf __pycache__
