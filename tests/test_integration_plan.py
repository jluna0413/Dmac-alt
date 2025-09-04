import os
from dmac.client import DmacClient


def test_save_plan_against_stub():
    # allow test to pick up BYTEROVER_MCP_URL from env, default is stub
    client = DmacClient()
    plan = {"name": "demo-plan", "tasks": []}
    resp = client.save_implementation_plan(plan)
    assert resp.get("ok") is True
    assert resp.get("action") == "byterover-save-implementation-plan"
    assert resp.get("received", {}).get("plan", {}).get("name") == "demo-plan"
