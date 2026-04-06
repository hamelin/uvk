from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from jupyter_client.manager import (
    BlockingKernelClient,
    KernelManager,
    start_new_kernel,
)
from jupyter_client.kernelspec import KernelSpecManager
from pathlib import Path
import pytest  # noqa
import subprocess as sp
import sys
import tomllib
from uuid import uuid4
from uv import find_uv_bin

from uvk.__main__ import prepare_kernelspec

from . import cook


@pytest.fixture(scope="session")
def kernelspec() -> Iterator[str]:
    """
    This is session-scoped since it is only used by a session-scoped kernel instantiation.
    """
    mgr = KernelSpecManager()
    name = f"uvk-{uuid4()}"
    with prepare_kernelspec(name, "UVK unit test") as dir_kernelspec:
        d = mgr.install_kernel_spec(str(dir_kernelspec), name, prefix=sys.prefix)

    yield name

    mgr.remove_kernel_spec(name)
    assert not Path(d).is_dir()


@dataclass
class KernelManagerAndClient:
    manager: KernelManager
    client: BlockingKernelClient


@pytest.fixture(scope="session")
def kernel(kernelspec: str) -> Iterator[KernelManagerAndClient]:
    """\
    Sets up the kernel manager and client that gets reused for UVK kernel tests. A previous simpler
    implementation had this fixture regularly-scoped, creating a whole new kernel for every test.
    However, Jupyter kernel managers truly expect to run only once in their process' life cycle,
    deferring the clean-up of various resources to a `atexit` handler. That implementation would
    thus "leak" file handles (wrapped in IP sockets), causing a **Too many open files** (errno 24)
    after enough tests involving the fixture.

    The current implementation, instead, keeps the same kernel manager for all unit tests,
    but explicitly restarts the kernel at the start of every unit test that requires the kernel
    client. Kernel restarting is a common operation for kernel managers that does not leak open
    files.

    This restarting approach explains why the first unit test requiring the kernel client fixture
    takes so long to run: it starts a kernel process _twice_.
    """
    km, kc = start_new_kernel(kernel_name=kernelspec)
    yield KernelManagerAndClient(manager=km, client=kc)
    km.shutdown_kernel()


@pytest.fixture
def client_kernel(kernel: KernelManagerAndClient) -> BlockingKernelClient:
    kernel.manager.restart_kernel()
    return kernel.client


ResultExec = dict
Outputs = dict[str, list[str]]


def execute(client: BlockingKernelClient, code: str) -> tuple[ResultExec, Outputs]:
    outputs: Outputs = {}

    def store_output(msg):
        if msg["msg_type"] == "stream":
            outputs.setdefault(msg["content"].get("name", "unknown"), []).append(
                msg["content"].get("text", "")
            )
        elif msg["msg_type"] == "display_data":
            for mime_type, content in msg.get("content", {}).get("data", {}).items():
                outputs.setdefault(mime_type, []).append(content)

    r = client.execute_interactive(code, output_hook=store_output)
    return r, {
        stream: "\n".join([chunk.strip() for chunk in chunks]).strip().splitlines()
        for stream, chunks in outputs.items()
    }


def test_client_hello(client_kernel: BlockingKernelClient) -> None:
    _, outputs = execute(client_kernel, "print('hello world')")
    assert outputs == {"stdout": ["hello world"]}


def test_load_ext(client_kernel: BlockingKernelClient) -> None:
    def magics(kind: str) -> set[str]:
        _, outputs = execute(
            client_kernel,
            f"""
            for m in get_ipython().magics_manager.magics["{kind}"].keys():
                print(m)
            """,
        )
        return set(outputs["stdout"])

    assert not ({"require_python", "dependencies"} <= magics("line"))
    assert not ({"script_metadata", "dependencies"} <= magics("cell"))
    client_kernel.execute_interactive("%load_ext uvk")
    assert {"require_python", "dependencies"} <= magics("line")
    assert {"script_metadata", "dependencies"} <= magics("cell")


@pytest.fixture
def client_uvk(client_kernel: BlockingKernelClient) -> BlockingKernelClient:
    client_kernel.execute_interactive("%load_ext uvk")
    return client_kernel


def test_require_python_satisfied(client_uvk: BlockingKernelClient) -> None:
    major, minor, *_ = sys.version_info
    r, outputs = execute(
        client_uvk,
        f"""
        %require_python >={major}.{minor}
        print(5)
        """,
    )
    assert r.get("content", {}).get("status", "") == "ok"
    assert outputs["stdout"] == ["5"]


def test_require_python_not_satisfied(client_uvk: BlockingKernelClient) -> None:
    major, minor, micro, *_ = sys.version_info
    r, outputs = execute(
        client_uvk,
        f"""
        %require_python <{major}.{minor}.{micro}
        print(5)
        """,
    )
    assert r.get("content", {}).get("status", "") == "error"
    assert r.get("content", {}).get("ename", "") == "PythonRequirementNotSatisfied"
    assert not outputs


def test_require_python_bad_specifier(client_uvk: BlockingKernelClient) -> None:
    r, outputs = execute(
        client_uvk,
        """
        %require_python asdf
        print(5)
        """,
    )
    assert r.get("content", {}).get("status", "") == "error"
    assert r.get("content", {}).get("ename", "") == "InvalidSpecifier"
    assert not outputs


def imports2cell(*imports: str) -> str:
    return "\n".join([*[f"import {imp}" for imp in imports], "print(5)"])


@pytest.mark.parametrize(
    "imports,expected_raw",
    [
        (
            (),
            """\
            print(5)
            """,
        ),
        (
            ("pytest",),
            """\
            import pytest
            print(5)
            """,
        ),
        (
            ("numpy as np", "joblib as jl"),
            """\
            import numpy as np
            import joblib as jl
            print(5)
            """,
        ),
    ],
)
def test_imports2cell(imports: tuple[str, ...], expected_raw: str):
    assert cook(expected_raw) == imports2cell(*imports)


def import_np_jl(client: BlockingKernelClient) -> tuple[ResultExec, Outputs]:
    return execute(client, imports2cell("numpy as np", "joblib as jl"))


def check_import_np_jl_fails(client: BlockingKernelClient) -> None:
    r, outputs = import_np_jl(client)
    assert r.get("content", {}).get("status", "") == "error"
    assert r.get("content", {}).get("ename", "") == "ModuleNotFoundError"


def check_import_np_jl_succeeds(client: BlockingKernelClient) -> None:
    r, outputs = import_np_jl(client)
    assert r.get("content", {}).get("status", "") == "ok"
    assert outputs.get("stdout") == ["5"]


@pytest.mark.parametrize(
    "dependencies_invocation",
    [
        """\
        %dependencies numpy scipy>1.11 scikit-learn==1.8.0
        """,
        """\
        %%dependencies
        numpy
        scikit-learn==1.8.0
        scipy>1.11
        """,
    ],
)
def test_dependencies(client_uvk: BlockingKernelClient, dependencies_invocation: str) -> None:
    check_import_np_jl_fails(client_uvk)
    _, outputs = execute(
        client_uvk,
        cook(dependencies_invocation),
    )
    assert "text/markdown" not in outputs
    check_import_np_jl_succeeds(client_uvk)


@pytest.mark.parametrize(
    "dependencies_invocation",
    [
        """
        %%dependencies numpy pandas
        scipy>1.11
        scikit-learn==1.8.0
        """,
        """
        %%dependencies
        numpy    \tpandas
        \t\tscipy>1.11
            scikit-learn==1.8.0
        """,
    ],
)
def test_dependencies_normalized(
    client_uvk: BlockingKernelClient, dependencies_invocation: str
) -> None:
    check_import_np_jl_fails(client_uvk)
    _, outputs = execute(
        client_uvk,
        cook(dependencies_invocation),
    )
    assert [
        (
            "Requirement specifications are irregular. They will be processed as "
            "if they had been supplied in the following form:"
        ),
        "",
        "```",
        "%%dependencies",
        "numpy",
        "pandas",
        "scipy>1.11",
        "scikit-learn==1.8.0",
        "```",
    ] == outputs.get("text/markdown", [])
    check_import_np_jl_succeeds(client_uvk)


def test_script_metadata_python_unsatisfied(client_uvk: BlockingKernelClient) -> None:
    r, _ = execute(
        client_uvk,
        cook("""\
            %%script_metadata
            # /// script
            # require-python = "==3.8.4"
            # ///
            """),
    )
    content = r.get("content", {})
    assert content.get("status", "") == "error"
    assert content.get("ename", "") == "PythonRequirementNotSatisfied"


@pytest.mark.parametrize("extraneous", [[], ["", "  ", "extraneous"]])
def test_script_metadata_add_dependencies(
    client_uvk: BlockingKernelClient, extraneous: list[str]
) -> None:
    check_import_np_jl_fails(client_uvk)
    r, outputs = execute(
        client_uvk,
        cook(
            "\n".join(
                [
                    cook(
                        """\
                        %%script_metadata
                        # /// script
                        # require-python = ">=3.10"
                        # dependencies = [
                        #     "numpy",
                        #     "scipy>1.11",
                        #     "scikit-learn==1.8.0",
                        # ]
                        # ///
                        """.rstrip(),
                    ),
                    *[f"# {line}" for line in extraneous],
                ]
            ),
        ),
    )
    assert r.get("content", {}).get("status", "") == "ok"
    if extraneous:
        assert any("trailing lines" in line for line in outputs.get("stderr", []))
    check_import_np_jl_succeeds(client_uvk)


def test_uv_magic_pip_install(client_uvk: BlockingKernelClient) -> None:
    check_import_np_jl_fails(client_uvk)
    r, _ = execute(
        client_uvk,
        cook(
            """\
            %uv pip install numpy scipy>1.11 scikit-learn==1.8.0
            """
        ),
    )
    assert r.get("content", {}).get("status", "") == "ok"
    check_import_np_jl_succeeds(client_uvk)


def test_uv_magic_run(client_uvk: BlockingKernelClient) -> None:
    r, outputs = execute(
        client_uvk,
        cook(
            """\
            %uv run python -c 'import os; print(os.environ["VIRTUAL_ENV"])'
            import os
            print(os.environ["VIRTUAL_ENV"])
            """
        ),
    )
    assert r.get("content", {}).get("status", "") == "ok"
    stdout = outputs["stdout"]
    assert len(stdout) >= 2
    assert stdout[0] == stdout[1]


def check_suffix_uv_interromark(client_uvk: BlockingKernelClient, suffix_expected: str) -> None:
    r, _ = execute(client_uvk, "%uv?\n")
    content = r.get("content", {})
    assert content.get("status", "") == "ok"
    output = "\n".join(
        element.get("data", {}).get("text/plain", "") for element in content.get("payload", [])
    )
    assert output.strip().endswith(suffix_expected)


def test_restore_uv_magick(client_uvk: BlockingKernelClient) -> None:
    check_suffix_uv_interromark(client_uvk, "uvk/__init__.py")
    r, _ = execute(client_uvk, "%restore_uv\n")
    assert r.get("content", {}).get("status", "") == "ok"
    check_suffix_uv_interromark(client_uvk, "IPython/core/magics/packaging.py")


def make_project(home: Path) -> None:
    sp.run(
        [
            find_uv_bin(),
            "init",
            "--name",
            home.name,
            "--python",
            sys.executable,
            "--lib",
            "--no-description",
            "--author-from",
            "none",
            "--vcs",
            "none",
            "--build-backend",
            "setuptools",
            "--no-readme",
            "--no-pin-python",
            str(home),
        ],
    ).check_returncode()
    sp.run([find_uv_bin(), "add", "--project", str(home), "requests"]).check_returncode()
    sp.run([find_uv_bin(), "version", "--project", str(home), "0.0.2"]).check_returncode()


@pytest.fixture
def project_haha(tmp_path: Path) -> Path:
    make_project(tmp_path / "haha")
    return tmp_path / "haha"


@contextmanager
def import_before_after_project(
    client_uvk: BlockingKernelClient,
    project: Path,
    name_import: str,
) -> Iterator[None]:
    r, _ = execute(client_uvk, f"import {name_import}\n")
    assert r.get("content", {}).get("status", "") == "error"
    r, _ = execute(client_uvk, f"%project {project}\n")
    assert r.get("content", {}).get("status", "") == "ok"
    yield None
    r, _ = execute(client_uvk, f"import {name_import}\n")
    assert r.get("content", {}).get("status", "") == "ok"


def test_project_haha(client_uvk: BlockingKernelClient, project_haha: Path) -> None:
    with import_before_after_project(client_uvk, project_haha, "requests"):
        pass


def test_project_add_dependency(client_uvk: BlockingKernelClient, project_haha: Path) -> None:
    with import_before_after_project(client_uvk, project_haha, "xonsh"):
        r, _ = execute(client_uvk, "%uv add xonsh\n")
        assert r.get("content", {}).get("status", "") == "ok"
        with (project_haha / "pyproject.toml").open(mode="rb") as file:
            pyproject = tomllib.load(file)
            dependencies = pyproject.get("project", {}).get("dependencies", [])
            for name in ["requests", "xonsh"]:
                assert any(dep.startswith(name) for dep in dependencies)


def test_project_add_remove_breaks_stuff(
    client_uvk: BlockingKernelClient, project_haha: Path
) -> None:
    r, output = execute(
        client_uvk,
        cook(
            """\
            from pathlib import Path
            import sys
            prefix = Path(sys.prefix)
            print(sys.prefix)
            assert (prefix / "bin" / "uv").is_file()
            import uv
            print(uv.find_uv_bin())
            """
        ),
    )
    assert r.get("content", {}).get("status", "") == "ok"
    prefix, path_uv = output["stdout"]
    assert Path(path_uv) == Path(prefix) / "bin" / "uv"

    r, _ = execute(client_uvk, f"%project {project_haha}\n")
    assert r.get("content", {}).get("status", "") == "ok"
    r, _ = execute(client_uvk, "%uv add aiohttp pandas")
    assert r.get("content", {}).get("status", "") == "ok"
    r, _ = execute(client_uvk, "%uv remove requests\n")
    assert r.get("content", {}).get("status", "") == "ok"
    r, output = execute(client_uvk, "uv.find_uv_bin()")
    content = r.get("content", {})
    assert content.get("status", "") == "error"
    assert content.get("ename", "") == "UvNotFound"


def test_project_import_package(client_uvk: BlockingKernelClient, project_haha: Path) -> None:
    with import_before_after_project(client_uvk, project_haha, "haha"):
        pass
    r, output = execute(client_uvk, "print(haha.hello())")
    assert r.get("content", {}).get("status", "") == "ok"
    assert "Hello from haha!" == "\n".join(output["stdout"]).strip()


def test_project_immutable_once_set(client_uvk: BlockingKernelClient, project_haha: Path) -> None:
    with import_before_after_project(client_uvk, project_haha, "requests"):
        r, _ = execute(client_uvk, "%project\n")
        assert r.get("content", {}).get("status", "") == "error"
