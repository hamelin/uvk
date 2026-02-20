from collections.abc import Iterator
from jupyter_client.manager import (
    BlockingKernelClient,
    start_new_kernel,
)
from jupyter_client.kernelspec import KernelSpecManager
import pytest  # noqa
import sys
from uuid import uuid4

from uvk.__main__ import prepare_kernelspec


@pytest.fixture
def installed_kernel() -> str:
    name = f"uvk-{uuid4()}"
    with prepare_kernelspec(name, "UVK unit test") as dir_kernelspec:
        KernelSpecManager().install_kernel_spec(
            str(dir_kernelspec), name, prefix=sys.prefix
        )
    return name


@pytest.fixture
def client_kernel(installed_kernel: str) -> Iterator[BlockingKernelClient]:
    km, kc = start_new_kernel(startup_timeout=10.0, kernel_name=installed_kernel)
    yield kc
    km.shutdown_kernel()


def execute(
    client: BlockingKernelClient, code: str, timeout: float = 10.0
) -> dict[str, list[str]]:
    outputs: dict[str, list[str]] = {}

    def store_output(msg):
        if msg["msg_type"] == "stream":
            outputs.setdefault(msg["content"].get("name", "unknown"), []).append(
                msg["content"].get("text", "")
            )

    client.execute_interactive(code, timeout=timeout, output_hook=store_output)
    return {
        stream: "\n".join(chunks).strip().split("\n")
        for stream, chunks in outputs.items()
    }


def test_client_hello(client_kernel: BlockingKernelClient) -> None:
    assert execute(client_kernel, "print('hello world')") == {"stdout": ["hello world"]}
