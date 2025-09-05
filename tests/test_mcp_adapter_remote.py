import json
from unittest.mock import patch, MagicMock

import pytest
import requests
from src.mcp_adapter.client import ByteroverClient


@patch("src.mcp_adapter.client.requests.sessions.Session.post")
def test_remote_create_project(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"success": True, "project_id": "proj-1"}

    client = ByteroverClient(endpoint="http://localhost:8051", extension_id="byterover.byterover", auth_token="tok-123")
    res = client.byterover_create_project("Test Project", "desc")
    assert res["success"] is True
    assert res["project_id"] == "proj-1"
    mock_post.assert_called_once()
    # assert headers passed
    args, kwargs = mock_post.call_args
    headers = kwargs.get("headers", {})
    assert headers.get("X-Byterover-Extension") == "byterover.byterover"
    assert headers.get("Authorization") == "Bearer tok-123"


@patch("src.mcp_adapter.client.requests.sessions.Session.post")
def test_remote_create_task(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"success": True, "task_id": "task-1"}

    client = ByteroverClient(endpoint="http://localhost:8051", extension_id="byterover.byterover", auth_token="tok-123")
    res = client.byterover_create_task("proj-1", "Do thing", "desc", assignee="AI IDE Agent", task_order=10)
    assert res["success"] is True
    assert res["task_id"] == "task-1"
    assert mock_post.call_count == 1
    args, kwargs = mock_post.call_args
    headers = kwargs.get("headers", {})
    assert headers.get("X-Byterover-Extension") == "byterover.byterover"
    assert headers.get("Authorization") == "Bearer tok-123"


@patch("src.mcp_adapter.client.requests.sessions.Session.post")
def test_remote_retrieve_active_plans(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"success": True, "plans": []}

    client = ByteroverClient(endpoint="http://localhost:8051", extension_id="byterover.byterover", auth_token="tok-123")
    res = client.byterover_retrieve_active_plans()
    assert res["success"] is True
    assert isinstance(res["plans"], list)
    args, kwargs = mock_post.call_args
    headers = kwargs.get("headers", {})
    assert headers.get("X-Byterover-Extension") == "byterover.byterover"
    assert headers.get("Authorization") == "Bearer tok-123"


@patch("src.mcp_adapter.client.requests.sessions.Session.post")
def test_remote_retry_backoff(mock_post):
    # first call raises, second returns success
    def side_effect(url, json, timeout, headers=None):
        if not hasattr(side_effect, "count"):
            side_effect.count = 0
        side_effect.count += 1
        if side_effect.count == 1:
            raise requests.exceptions.RequestException("network")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True, "project_id": "proj-retry"}
        return mock_resp

    mock_post.side_effect = side_effect
    client = ByteroverClient(endpoint="http://localhost:8051", extension_id="byterover.byterover", auth_token="tok-123", max_retries=2, backoff_factor=0.1)
    res = client.byterover_create_project("Retry Project")
    assert res["success"] is True
    assert res["project_id"] == "proj-retry"
