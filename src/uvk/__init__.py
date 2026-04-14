"""
This IPython extension provides [magics](https://ipython.readthedocs.io/en/stable/interactive/magics.html)
to enforce the dependency requirements of a **uv**-isolated IPython kernel,
at **uv** speed.
Load the extension with a cell such as:

```ipython
%load_ext uvk
```
"""

from collections.abc import Iterable
from IPython.core.interactiveshell import InteractiveShell
from IPython.display import display, Markdown
import logging as lg
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from pathlib import Path
import shlex
import subprocess as sp
import sys
from tempfile import NamedTemporaryFile
from typing import Any, cast, overload, Protocol
from uv import find_uv_bin
from warnings import warn

from ._parse import parse_dependencies, parse_script_metadata
from .util import uv_

LOG = lg.getLogger(__name__)
PROJECT: list[str] = []


class NamedMagic(Protocol):
    __name__: str

    @overload
    def __call__(self, line_or_cell: str = "") -> Any: ...

    @overload
    def __call__(self, line: str, cell: str = "") -> Any: ...


MAGICS_OVERRIDEN: dict[str, NamedMagic] = {}


def load_ipython_extension(shell: InteractiveShell) -> None:
    for magic_, kind, is_overriding in [
        (require_python, "line", False),
        (script_metadata, "cell", False),
        (dependencies, "line_cell", False),
        (uv(shell), "line", True),
        (restore_uv(shell), "line", False),
        (project(shell), "line", False),
    ]:
        magic = cast(NamedMagic, magic_)
        if is_overriding:
            MAGICS_OVERRIDEN[magic.__name__] = shell.magics_manager.magics[kind][magic.__name__]
        shell.register_magic_function(func=magic, magic_kind=kind, magic_name=magic.__name__)  # type: ignore


def script_metadata(line: str, cell: str) -> None:
    """
    PyPA [script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/) in a cell.

    **Usage:**

    ```ipython
    %%script_metadata
    # /// script
    # requires-python = "..."
    # dependencies = [
    #     "list",
    #     "of",
    #     "package",
    #     "requiments",
    # ]
    # ///
    ```

    Processes the cell as script metadata,
    effectively checking a Python interpreter specification is met by the
    running interpreter, and deploys the packages specified through
    the `dependencies` field.

    Example:
        ```ipython
        %%script_metadata
        # /// script
        # requires-python = ">=3.13"
        # dependencies = ["numpy", "pandas>=3"]
        # ///
        ```
        <div class="bgpre bgred">
        <pre>
        Resolved <strong>4 packages</strong> in 48ms
        Installed <strong>2 packages</strong> in 59ms
         <span style="color: green">+</span> <strong>numpy</strong>==2.4.4
         <span style="color: green">+</span> <strong>pandas</strong>==3.0.2
        </pre>
        </div>

    Raises:
        PythonRequirementNotSatisfied: `requires-python` specification was not satisfied.
    """
    if line:
        warn(
            "Non-empty line argument (on the right of %%script_metadata) is ignored",
            category=RuntimeWarning,
        )
    sm = parse_script_metadata(str(cell))
    if "require-python" in sm:
        _require_python(sm["require-python"])
    if "dependencies" in sm:
        _install_requirements(sm["dependencies"])


class PythonRequirementNotSatisfied(Exception):
    """
    Raised when the current Python interpreter is checked against a
    version specification, and fails to satisfy it.

    Attributes:
        spec:    Specification that was not satisfied.
        version: Version of this Python interpreter checked against the specification.
    """

    def __init__(self, spec: str, version: str) -> None:
        super().__init__(
            (
                f"Python version specification {spec} not satisfied: "
                f"current interpreter is version {version}"
            )
        )
        self.spec = spec
        self.version = version


def _require_python(spec: str) -> None:
    version, *_ = sys.version.split()
    if version not in SpecifierSet(spec):
        raise PythonRequirementNotSatisfied(spec, version)
    LOG.info(f"Current Python version {version} satisfies specification {spec}")


def require_python(line: str = "") -> None:
    """\
    Check Python satisfies the given specification.

    Usage:

    ```ipython
    %require_python >=3.11
    ```
    
    Verifies that the current Python interpreter satisfies the given version
    specification, and raises [PythonRequirementNotSatisfied](#pythonrequirementnotsatisfied)
    if it doesn't.
    Remark how, contrary to **uv run**'s handling of script metadata,
    this cell magic cannot select an alternative Python version that satisfies
    the specification. **uv run** parses the script metadata ahead of starting
    the Python interpreter. In contrast, this magic is computed from the
    already-running, and IPython does not manage the Python interpreter.
    See [this deep dive](../deepdives/uv-uvkernel-uvk.md) for more details on
    enforcing a Python interpreter requirement.

    Example:
        ```ipython
        import sys
        sys.version
        ```
        <div class="bgpre">
        <pre>
        3.12.11 (main, Jul 23 2025, 00:18:05) [Clang 20.1.4 ]
        </pre>
        </div>
        ```ipython
        %require_python >=3.13
        ```
        <div class="bgpre bgred">
        <pre>
        <span class="red">--------------------------------------------------------------------------
        PythonRequirementNotSatisfied</span>             Traceback (most recent call last)
        ...
        </pre>
        </div>
    """
    _require_python(str(line))


def dependencies(line: str, cell: str = "") -> None:
    """
    Deploy a set of package requirements.

    Usage:

    ```ipython
    %%dependencies
    package+constraint
    ...
    ```

    Deploys a set of package requirements using `uv pip install`.
    Contrary to `requirements.txt`, there should be **no blank space**
    between the package name and the package version.

    Example:
        ```ipython
        %%dependencies
        duckdb
        requests<2.33
        pygments>=2.18
        ```
        <div class="bgpre bgred">
        <pre>
        Resolved <span class="bold">7 packages</span> in 4ms
        Installed <span class="bold">6 packages</span> in 4ms
         <span class="green">+</span> <span class="bold">certifi</span>==2026.2.25
         <span class="green">+</span> <span class="bold">charset</span>-normalizer==3.4.7
         <span class="green">+</span> <span class="bold">duckdb</span>==1.5.2
         <span class="green">+</span> <span class="bold">idna</span>==3.11
         <span class="green">+</span> <span class="bold">requests</span>==2.32.5
         <span class="green">+</span> <span class="bold">urllib3</span>==2.6.3
        </pre>
        </div>
    """
    dependencies_raw = (f"{line.strip()}\n{cell}" if line and cell else line or cell).strip()
    dependencies_normalized = list(parse_dependencies(dependencies_raw))
    if cell:
        if line or dependencies_normalized != [
            line.strip() for line in dependencies_raw.split("\n")
        ]:
            LOG.debug("Dependencies are irregular")
            display(
                Markdown(
                    "\n".join(
                        [
                            (
                                "Requirement specifications are irregular. "
                                "They will be processed as if they had been supplied "
                                "in the following form:"
                            ),
                            "",
                            "```",
                            "%%dependencies",
                            *dependencies_normalized,
                            "```",
                        ]
                    )
                )
            )

    _install_requirements(dependencies_normalized)


def _install_requirements(requirements: Iterable[str]) -> None:
    with NamedTemporaryFile("wt", encoding="utf-8") as file:
        for dep in requirements:
            Requirement(dep)  # Will raise an exception on invalid requirements.
            print(dep, file=file)
        file.flush()

        cmd = [find_uv_bin(), "pip", "install", "--requirements", file.name]
        LOG.debug("Run " + " ".join(cmd))
        sp.run(cmd).check_returncode()


def uv(shell: InteractiveShell) -> NamedMagic:
    """
    Spawn and run **uv**.

    Usage:

    ```ipython
    %uv command arguments
    ```

    This reimplementation of IPython's own `%uv` line magic takes extra care
    to set the active environment (using the `--active`) flag for **uv**
    subcommands that use it, as well as set the Python executable so as to
    avoid switching away from the interpreter running this kernel.
    If this override of IPython's `%uv` is undesired and one would rather
    get it back, simply run [`%restore_uv`](#restore_uv).

    Example:
        ```ipython
        %uv run python -c "import os; print(os.environ['VIRTUAL_ENV'])"
        ```
        <div class="bgpre">
        <pre>/home/heyhey/.cache/uv/builds-v0/.tmpoPZabc</pre>
        </div>
        ```ipython
        %uv run --isolated python -c "import os; print(os.environ['VIRTUAL_ENV'])"
        ```
        <div class="bgpre">
        <pre>
        Installed <span class="bold">37 packages</span> in 92ms
        /home/heyhey/.cache/uv/builds-v0/.tmpFlSlPn
        </pre>
        </div>
    """

    def _uv(line: str = "") -> None:
        args = shlex.split(line)
        shell.system(" ".join(shlex.quote(token) for token in uv_(args, PROJECT)))

    _uv.__name__ = "uv"
    return cast(NamedMagic, _uv)


def restore_uv(shell: InteractiveShell) -> NamedMagic:
    """
    Restore the standard IPython `%uv` magic.

    Usage:

    ```ipython
    %restore_uv
    ```
    """

    def restore_uv(line: str = "") -> None:
        if "uv" in shell.magics_manager.magics["line"]:
            if "uv" in MAGICS_OVERRIDEN:
                uv_previous = MAGICS_OVERRIDEN.pop("uv")
                if callable(uv_previous):
                    shell.register_magic_function(  # ty: ignore[missing-argument]
                        func=uv_previous,
                        magic_kind="line",
                        magic_name="uv",
                    )
                    print(
                        "Restored the implementation of %uv that the uvk extension had overriden."
                    )
                else:
                    print(
                        "WARNING: the %uv magic that the uvk extension overrode does not look like a Python callable. Will not attempt to restore it."
                    )
            else:
                print(
                    "The current %uv implementation was not registered by the uvk extension. No op."
                )
        else:
            print(
                "Strange: no %uv line magic is present. You may need to restart your kernel to restore this standard IPython functionality."
            )

    restore_uv.__name__ = "restore_uv"
    return cast(NamedMagic, restore_uv)


def project(shell: InteractiveShell) -> NamedMagic:
    """
    Attach a **uv** project to the kernel.

    Usage:

    ```ipython
    %project [path to project]
    ```

    If no path is provided, the current directory is used as project anchor.

    This sets internal parameters so that invocations of `%uv` will automatically
    set the `--project` flag (as appropriate to subcommand) and, thus direct
    **uv** tasks to the chosen project.
    It also **uv sync**s the isolated environment to that project's dependencies.

    Note:
        This magic can be used **only once** during the lifetime of a kernel
        process. To change the project, the kernel must be restarted.

    Raises:
        ValueError: when this magic is called again after the project has been set.

    Example:
        ```ipython
        from pathlib import Path
        dir_mock_project = Path.home() / "uvk_mock_project"
        %uv init --name mock_project --package --bare --no-description {dir_mock_project}
        ```
        <div class="bgpre">
        <pre>
        Initialized project `<span class="cyan">mock-project</span>` at `<span class="cyan">/home/heyhey/uvk-mock-project</span>`
        </pre>
        </div>
        ```ipython
        %project {dir_mock_project}
        ```
        <div class="bgpre">
        <pre>
        Resolved <span class="bold">1 package</span> in 6ms
        Prepared <span class="bold">1 package</span> in 5ms
        Installed <span class="bold">1 package</span> in 2ms (from file:///home/heyhey/uvk-m
         <span class="green">+</span> <span class="bold">mock-project</span>==0.1.0 (from file:///home/heyhey/uvk-mock-project)
        </pre>
        </div>
        ```ipython
        %uv add pandas requests
        import pandas as pd  # Will just import without issue
        %uv tree
        ```
        <div class="bgpre">
        <pre>
        Resolved <span class="bold">11 packages</span> in 82ms
        Prepared <span class="bold">1 package</span> in 5ms
        Uninstalled <span class="bold">1 package</span> in 0.91ms
        Installed <span class="bold">8 packages</span> in 57ms
         <span class="green">+</span> <span class="bold">certifi</span>==2026.2.25
         <span class="green">+</span> <span class="bold">charset-normalizer</span>==3.4.7
         <span class="green">+</span> <span class="bold">idna</span>==3.11
         <span class="yellow">~</span> <span class="bold">mock-project</span>==0.1.0 (from file:///home/heyhey/uvk-mock-project)
         <span class="green">+</span> <span class="bold">numpy</span>==2.4.4
         <span class="green">+</span> <span class="bold">pandas</span>==3.0.2
         <span class="green">+</span> <span class="bold">requests</span>==2.33.1
         <span class="green">+</span> <span class="bold">urllib3</span>==2.6.3
        Using CPython 3.12.11 interpreter at: /home/heyhey/.cache/uv/builds-v0/.tmpculMrO/bin/python
        Resolved <span class="bold">11 packages</span> in 0.76ms
        mock-project v0.1.0
        ├── pandas v3.0.2
        │   ├── numpy v2.4.4
        │   └── python-dateutil v2.9.0.post0
        │       └── six v1.17.0
        └── requests v2.33.1
            ├── certifi v2026.2.25
            ├── charset-normalizer v3.4.7
            ├── idna v3.11
            └── urllib3 v2.6.3
        </pre>
        </div>
    """

    def _project(line: str = "") -> None:
        if PROJECT:
            raise ValueError(
                "Once set, the kernel's project is immutable. Thus, you may not invoke %project more than once."
            )
        PROJECT.extend(["--project", str(Path(line or ".").resolve())])
        uv(shell)("sync --inexact")

        # uv sync against the chosen project adds that project's editable modules to the site
        # packages of our isolated environment. Python usually sets up loaders for these as it
        # starts up, so we must emulate this behaviour.
        #
        # An editable package named `blah`, at version x.y.z, will be associated to a directory
        # named `blah-x.y.z.dist-info`, as well as either one of two files:
        #
        #     blah.pth                      or
        #     __editable__.blah-x.y.z.pth
        #
        # In both cases, this .pth file contains the path to the directory with the source of the
        # package, which we must add to sys.path. However, this .pth extension is also sometimes
        # used for sourceable Python files by other bits of code! So we must be careful: as we
        # hit .pth files wondering whether we should stick their contents in sys.path, let's make
        # sure they correspond to a .dist-info to a directory, and that their contents is a valid
        # directory. (Very silly to overload .pth, honestly. Not a fan.)
        prefix = Path(sys.prefix)
        for path in (Path(p) for p in sys.path):
            if prefix in path.parents and all(
                (path / f"_virtualenv.{ext}").is_file() for ext in ["py", "pth"]
            ):
                for pth in path.glob("*.pth"):
                    if pth.name.startswith("__editable__."):
                        name_version = pth.with_suffix("").name[len("__editable__.") :]
                        pat_dist_info = f"{name_version}.dist-info"
                    else:
                        pat_dist_info = f"{pth.with_suffix('').name}-*.dist-info"
                    if any(path.glob(pat_dist_info)):
                        path_source = pth.read_text(encoding="utf-8").strip()
                        if Path(path_source).is_dir() and path_source not in sys.path:
                            sys.path.append(path_source)

    _project.__name__ = "project"
    return cast(NamedMagic, _project)
