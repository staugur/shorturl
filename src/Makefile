.PHONY: help

help:
	@echo "test    run test examples"
	@echo "run     start a server for develpment"

test:
	python -m unittest discover -p "test_*.py"

run:
	export FLASK_ENV=development && python main.py
