import json
import requests
from pathlib import Path

import json
import requests
from pathlib import Path

from src.mcp_adapter.client import ByteroverClient


def test_headers_and_auth_sent():
    client = ByteroverClient(endpoint="https://api.local", extension_id="ext-123", auth_token="tok-xyz", max_retries=1)

    class FakeResponse(requests.Response):
        def __init__(self):
            super().__init__()
            self._content = json.dumps({"ok": True}).encode('utf-8')
            self.status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            if self._content is None:
                raise ValueError("Response content is None")
            return json.loads(self._content.decode('utf-8'))

    def fake_post(*args, **kwargs):
        headers = kwargs.get("headers")
        assert headers is not None
        assert headers.get("X-Byterover-Extension") == "ext-123"
        assert headers.get("Authorization") == "Bearer tok-xyz"
        return FakeResponse()

    client.session.post = fake_post
    res = client.byterover_save_implementation_plan({"title": "Plan"})
    assert res == {"ok": True}


def test_retry_exhaustion_writes_offline(tmp_path):
    # Use a non-functional endpoint and a short retry policy.
    client = ByteroverClient(endpoint="https://does.not.exist", offline_dir=str(tmp_path), max_retries=2, backoff_factor=0)

    def always_fail(*a, **k):
        raise requests.exceptions.ConnectionError("simulated")

    client.session.post = always_fail

    result = client.byterover_store_knowledge("important messages")
    assert result.get("success") is True
    offline_file = result.get("offline_file")
    assert offline_file
    p = Path(offline_file)
    assert p.exists()

    payload = json.loads(p.read_text(encoding="utf-8"))
    assert payload.get("action") == "byterover-store-knowledge"
    assert payload.get("payload") == {"messages": "important messages"}


def test_retry_attempts_count(tmp_path):
    client = ByteroverClient(endpoint="https://does.not.exist", offline_dir=str(tmp_path), max_retries=3, backoff_factor=0)
    counter = {"calls": 0}

    def failing_post(*a, **kw):
        counter["calls"] += 1
        raise requests.exceptions.ConnectionError("sim")

    client.session.post = failing_post
    res = client.byterover_store_knowledge("x")
    # it should have attempted max_retries times before writing offline
    assert counter["calls"] == 3
    assert res.get("success") is True
