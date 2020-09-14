.PHONY: check install develop test coverage lint flake


check:
	python setup.py check

install:
	python setup install

develop:
	python setup develop

test:
	pytest .

coverage:
	pytest --cov=origami .

lint:
	black .
	isort -y
	flake8 .

flake:
	flake8 .