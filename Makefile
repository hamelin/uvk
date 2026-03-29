UV_RUN = uv run --dev


all: test type pep8

tests: test

test: format
	$(UV_RUN) pytest $(and $(dbg),--last-failed --trace) $(and $(failfast),-x) $(and $(pdb),--pdb) $(and $(only),-k "$(only)") src

type: format
	$(UV_RUN) ty check src

pep8: format
	$(UV_RUN) ruff check src

format:
	$(UV_RUN) ruff format src

jupyterlab:
	uv run uvk --name uvk-test --display-name "UVK TEST" --sys-prefix $(UVK_ARGS)
	uv run --group proto jupyter lab --no-browser
