PYTHON := python3
APP := ai_review
UVICORN := uvicorn
PACKAGE_DIR := app
PORT ?= 8002

.PHONY: run dev lint fmt test pull-models clean

run:
	$(UVICORN) app.main:app --host 0.0.0.0 --port $(PORT)

dev:
	$(UVICORN) app.main:app --host 0.0.0.0 --port $(PORT) --reload

pull-models:
	./scripts/pull_models.sh

fmt:
	ruff format $(PACKAGE_DIR)

lint:
	ruff check $(PACKAGE_DIR)
	mypy $(PACKAGE_DIR)

test:
	pytest -q

compose-up:
	docker compose up --build

compose-down:
	docker compose down -v

compose-dev:
	docker compose up --build -d && docker compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".coverage" -delete
	find . -name "*.so" -delete

install:
	pip install -r requirements.txt

setup: install pull-models
