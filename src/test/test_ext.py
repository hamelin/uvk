from collections.abc import Iterator
from jupyter_client.manager import (
    BlockingKernelClient,
    start_new_kernel,
)
from jupyter_client.kernelspec import KernelSpecManager
from pathlib import Path
import pytest  # noqa
import sys
from textwrap import dedent
from uuid import uuid4

from uvk.__main__ import prepare_kernelspec

from . import cook


@pytest.fixture
def kernelspec() -> Iterator[str]:
    mgr = KernelSpecManager()
    name = f"uvk-{uuid4()}"
    with prepare_kernelspec(name, "UVK unit test") as dir_kernelspec:
        d = mgr.install_kernel_spec(str(dir_kernelspec), name, prefix=sys.prefix)

    yield name

    mgr.remove_kernel_spec(name)
    assert not Path(d).is_dir()


@pytest.fixture
def client_kernel(kernelspec: str) -> Iterator[BlockingKernelClient]:
    km, kc = start_new_kernel(startup_timeout=10.0, kernel_name=kernelspec)
    yield kc
    km.shutdown_kernel()


def execute(
    client: BlockingKernelClient, code: str, timeout: float = 10.0
) -> tuple[dict, dict[str, list[str]]]:
    outputs: dict[str, list[str]] = {}

    def store_output(msg):
        if msg["msg_type"] == "stream":
            outputs.setdefault(msg["content"].get("name", "unknown"), []).append(
                msg["content"].get("text", "")
            )
        elif msg["msg_type"] == "display_data":
            for mime_type, content in msg.get("content", {}).get("data", {}).items():
                outputs.setdefault(mime_type, []).append(content)

    r = client.execute_interactive(code, timeout=timeout, output_hook=store_output)
    return r, {
        stream: "\n".join([chunk.strip() for chunk in chunks]).strip().split("\n")
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


def import_externals(client: BlockingKernelClient) -> bool:
    r, outputs = execute(
        client,
        """
        import numpy as np
        import joblib as jl
        print(5)
        """,
    )
    return (
        r.get("content", {}).get("status", "") == "ok" and outputs["stdout"][-1] == "5"
    )


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
def test_dependencies(
    client_uvk: BlockingKernelClient, dependencies_invocation: str
) -> None:
    assert not import_externals(client_uvk)
    _, outputs = execute(
        client_uvk,
        dedent(dependencies_invocation.rstrip()),
    )
    assert "text/markdown" not in outputs
    assert import_externals(client_uvk)


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
    assert not import_externals(client_uvk)
    _, outputs = execute(
        client_uvk,
        dedent(dependencies_invocation.rstrip()),
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
    assert import_externals(client_uvk)
