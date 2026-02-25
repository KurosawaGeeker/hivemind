.PHONY: setup lint test run

setup:
	python -m pip install -r requirements-dev.txt

lint:
	python -m compileall base_agent.py echo.py elon.py henry.py main.py

test:
	pytest -q

run:
	python main.py
