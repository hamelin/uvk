UV_RUN = uv run --dev


all: test type pep8

tests: test

test:
	$(UV_RUN) pytest src

type:
	$(UV_RUN) mypy --ignore-missing-imports src

pep8:
	$(UV_RUN) flake8 src
