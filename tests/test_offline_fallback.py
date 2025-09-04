import json
import os
from pathlib import Path

import pytest

from dmac.client import DmacClient


def test_offline_fallback(tmp_path: Path):
    # choose an unused high port to simulate the MCP being unreachable
    base_url = "http://127.0.0.1:59999"
    offline_dir = tmp_path / "offline"
    client = DmacClient(base_url=base_url, offline_dir=str(offline_dir))
    plan = {"name": "will-fail", "tasks": []}

    with pytest.raises(Exception):
        client.save_implementation_plan(plan)

    # offline dir should contain exactly one failed_*.json file
    files = list(offline_dir.glob("failed_*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["path"] == "/byterover-save-implementation-plan"
    assert data["payload"]["plan"]["name"] == "will-fail"
