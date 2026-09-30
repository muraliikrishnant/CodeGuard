.PHONY: install lint test check benchmark frontend api

install:
	pip install -e ".[dev,frontend,benchmark]"

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

typecheck:
	mypy src/codeguard/

test:
	pytest -m "not live" --tb=short

check: lint typecheck test

benchmark:
	python benchmarks/corpus/plant.py
	python benchmarks/evaluate.py

api:
	uvicorn codeguard.api:app --reload --port 8000

frontend:
	cd frontend && npm run dev
