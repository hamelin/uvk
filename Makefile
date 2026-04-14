VERSIONS_PYTHON = 3.11 3.12 3.13 3.14
PYTHON_LOCAL = $(shell python -c "import sys; print(sys.executable)")
UV = uv $(1) --python $(subst local,$(PYTHON_LOCAL),$(notdir $(2))) --dev
UV_MKDOCS = uv run --all-extras mkdocs

every-check: every-check/local
every-check/%: test/% type/% pep8/%
	@true
all: $(foreach v,$(VERSIONS_PYTHON),every-check/$(v))

tests: test
test: test/local
test/%: format/%
	$(call UV,run,$@) pytest $(and $(only),$(if $(filter -,$(only)),--last-failed,-k $(only))) $(and $(fail1),-x) $(and $(pdb),--pdb) src

type: type/local
type/%: format/%
	$(call UV,run,$@) ty check src

pep8: pep8/local
pep8/%: format/%
	$(call UV,run,$@) ruff check src

format: format/local
format/%: sync/%
	$(call UV,run,$@) ruff format src

sync: sync/local
sync/%:
	$(call UV,sync,$@)

.SECONDARY:

jupyterlab:
	uv run uvk --name uvk-test --display-name "UVK TEST" --sys-prefix $(UVK_ARGS)
	uv run --group proto jupyter lab --no-browser

ipython:
	uv run --group proto ipython

banner: banner/local
banner/%:
	$(call UV,run,$@) --script banner.py

docs/build:
	$(UV_MKDOCS) build

docs/serve:
	$(UV_MKDOCS) serve --livereload --strict --watch src/uvk $(and $(address),--dev-addr $(address))
