import time
import os
import tempfile
import requests

from src.mcp_adapter.client import ByteroverClient


def test_client_posts_to_local_stub(tmp_path, stub_server):
    # start with a client pointing at the programmatic stub fixture
    endpoint = os.environ.get('BYTEROVER_MCP_URL', stub_server)
    client = ByteroverClient(endpoint=endpoint, offline_dir=str(tmp_path))

    # basic smoke calls — these will succeed only if the stub is running
    # byterover_create_project expects a title string
    resp = client.byterover_create_project('test-proj')
    assert resp.get('ok') is True

    # byterover_store_knowledge expects a messages string
    resp = client.byterover_store_knowledge('doc: sample')
    assert resp.get('ok') is True

    # save implementation plan accepts a dict payload
    resp = client.byterover_save_implementation_plan({'title': 'plan'})
    assert resp.get('ok') is True
