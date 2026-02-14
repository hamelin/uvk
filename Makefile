UV_RUN = uv run --dev


all: test type pep8

tests: test

test: black
	$(UV_RUN) pytest src

type: black
	$(UV_RUN) mypy --ignore-missing-imports src

pep8: black
	$(UV_RUN) flake8 src

black:
	$(UV_RUN) black src
