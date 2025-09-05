import json
from pathlib import Path

from src.mcp_adapter.client import ByteroverClient


def test_offline_save_plan(tmp_path):
    offline_dir = tmp_path / "offline"
    client = ByteroverClient(endpoint=None, offline_dir=str(offline_dir))
    plan = {"title": "Test Plan", "steps": ["a", "b"]}
    res = client.byterover_save_implementation_plan(plan)
    assert res["success"] is True
    offline_file = Path(res["offline_file"])
    assert offline_file.exists()
    content = json.loads(offline_file.read_text(encoding="utf-8"))
    assert content["action"] == "byterover-save-implementation-plan"
    assert content["payload"]["plan"]["title"] == "Test Plan"
