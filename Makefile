UV_RUN = uv run --dev

VERSIONS_PYTHON = 11 12 13 14
VERSION_DEFAULT = $(firstword $(VERSIONS_PYTHON))

every-check: every-check/$(VERSION_DEFAULT)
every-check/%: test/% type/% pep8/%
	@true
all: $(foreach v,$(VERSIONS_PYTHON),every-check/$(v))

tests: test
test: test/$(VERSION_DEFAULT)
test/%: format/%
	$(UV_RUN) pytest $(and $(dbg),--last-failed --trace) $(and $(failfast),-x) $(and $(pdb),--pdb) $(and $(only),-k "$(only)") src

type: type/$(VERSION_DEFAULT)
type/%: format/%
	$(UV_RUN) ty check src

pep8: pep8/$(VERSION_DEFAULT)
pep8/%: format/%
	$(UV_RUN) ruff check src

format: format/$(VERSION_DEFAULT)
format/%: sync/%
	$(UV_RUN) ruff format src

sync: sync/$(VERSION_DEFAULT)
sync/%:
	uv sync --dev --python 3.$(@F)

.SECONDARY:

jupyterlab:
	uv run uvk --name uvk-test --display-name "UVK TEST" --sys-prefix $(UVK_ARGS)
	uv run --group proto jupyter lab --no-browser

ipython:
	uv run --group proto ipython
