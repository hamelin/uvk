UV_RUN = uv run --dev


all: test type pep8

tests: test

test: black
	$(UV_RUN) pytest $(and $(failfast),-x) $(and $(pdb),--pdb) src

type: black
	$(UV_RUN) mypy --ignore-missing-imports src

pep8: black
	$(UV_RUN) flake8 src

black:
	$(UV_RUN) black src

jupyterlab:
	uv run uvk --name uvk-test --display-name "UVK TEST" -f --sys-prefix $(UVK_ARGS)
	uv run --group proto jupyter lab --no-browser
