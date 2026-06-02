# Convenience targets — usable via `make <target>` on Unix or in WSL.
.PHONY: install data train demo api dashboard test docker clean

install:
	pip install -r requirements.txt

data:
	python scripts/generate_sample_data.py

train:
	python scripts/train_all_models.py

demo:
	python scripts/run_pipeline.py

api:
	uvicorn src.api.main:app --reload --port 8000

dashboard:
	streamlit run src/dashboard/app.py

test:
	pytest -m "not slow" -v

test-all:
	pytest -v

docker:
	docker-compose up --build

clean:
	rm -rf data/models/*.joblib data/models/*.pt data/models/*.json
	rm -rf data/reports/*
	find . -type d -name __pycache__ -exec rm -rf {} +
