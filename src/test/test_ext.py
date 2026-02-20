from collections.abc import Iterator
from jupyter_client.manager import (
    BlockingKernelClient,
    start_new_kernel,
)
from jupyter_client.kernelspec import KernelSpecManager
from pathlib import Path
import pytest  # noqa
import sys
from uuid import uuid4

from uvk.__main__ import prepare_kernelspec


@pytest.fixture
def kernelspec() -> Iterator[str]:
    mgr = KernelSpecManager()
    name = f"uvk-{uuid4()}"
    with prepare_kernelspec(name, "UVK unit test", isolated=False) as dir_kernelspec:
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
        print(msg)
        if msg["msg_type"] == "stream":
            outputs.setdefault(msg["content"].get("name", "unknown"), []).append(
                msg["content"].get("text", "")
            )

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

    assert not ({"python_version", "dependencies"} <= magics("line"))
    assert not ({"script_metadata", "dependencies"} <= magics("cell"))
    client_kernel.execute_interactive("%load_ext uvk")
    assert {"python_version", "dependencies"} <= magics("line")
    assert {"script_metadata", "dependencies"} <= magics("cell")


@pytest.fixture
def client_uvk(client_kernel: BlockingKernelClient) -> BlockingKernelClient:
    client_kernel.execute_interactive("%load_ext uvk")
    return client_kernel


def test_python_version_satisfied(client_uvk: BlockingKernelClient) -> None:
    major, minor, *_ = sys.version_info
    r, outputs = execute(
        client_uvk,
        f"""
        %python_version >={major}.{minor}
        print(5)
        """,
    )
    assert r.get("content", {}).get("status", "") == "ok"
    assert outputs["stdout"] == ["5"]


def test_python_version_not_satisfied(client_uvk: BlockingKernelClient) -> None:
    major, minor, micro, *_ = sys.version_info
    r, outputs = execute(
        client_uvk,
        f"""
        %python_version <{major}.{minor}.{micro}
        print(5)
        """,
    )
    assert r.get("content", {}).get("status", "") == "error"
    assert r.get("content", {}).get("ename", "") == "PythonVersionNotSatisfied"
    assert not outputs


def test_python_version_bad_specifier(client_uvk: BlockingKernelClient) -> None:
    r, outputs = execute(
        client_uvk,
        """
        %python_version asdf
        print(5)
        """,
    )
    assert r.get("content", {}).get("status", "") == "error"
    assert r.get("content", {}).get("ename", "") == "InvalidSpecifier"
    assert not outputs
