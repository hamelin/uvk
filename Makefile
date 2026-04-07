VERSIONS_PYTHON = 3.11 3.12 3.13 3.14
PYTHON_LOCAL = python
UV = uv $(1) --python $(notdir $(2)) --dev

every-check: every-check/$(PYTHON_LOCAL)
every-check/%: test/% type/% pep8/%
	@true
all: $(foreach v,$(VERSIONS_PYTHON),every-check/$(v))

tests: test
test: test/$(PYTHON_LOCAL)
test/%: format/%
	$(call UV,run,$@) pytest $(and $(only),$(if $(subst -,,$(only)),-k $(only),--last-failed)) $(and $(failfast),-x) $(and $(pdb),--pdb) src

type: type/$(PYTHON_LOCAL)
type/%: format/%
	$(call UV,run,$@) ty check src

pep8: pep8/$(PYTHON_LOCAL)
pep8/%: format/%
	$(call UV,run,$@) ruff check src

format: format/$(PYTHON_LOCAL)
format/%: sync/%
	$(call UV,run,$@) ruff format src

sync: sync/$(PYTHON_LOCAL)
sync/%:
	$(call UV,sync,$@)

.SECONDARY:

jupyterlab:
	uv run uvk --name uvk-test --display-name "UVK TEST" --sys-prefix $(UVK_ARGS)
	uv run --group proto jupyter lab --no-browser

ipython:
	uv run --group proto ipython
