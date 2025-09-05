import os
import sys
import time
import subprocess
import socket
from pathlib import Path

import requests
import pytest


# Ensure repo root is importable for tests that import src/
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _find_free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    addr, port = s.getsockname()
    s.close()
    return port


@pytest.fixture(scope="session")
def stub_server():
    """Start the local mcp-stub via uvicorn on a free port and yield the base URL."""
    stub_dir = Path(__file__).resolve().parents[1]
    port = _find_free_port()
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--app-dir",
        str(stub_dir / "app"),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    proc = subprocess.Popen(cmd, cwd=str(stub_dir))
    url = f"http://127.0.0.1:{port}"

    # wait for readiness
    for _ in range(50):
        try:
            # endpoint is POST-only on the stub; send an empty JSON body to probe readiness
            r = requests.post(f"{url}/byterover-retrieve-active-plans", json={}, timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate()
        proc.wait(timeout=2)
        raise RuntimeError("mcp-stub did not start in time")

    yield url

    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
