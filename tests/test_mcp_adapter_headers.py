import json
from pathlib import Path


def test_headers_and_auth(monkeypatch, tmp_path):
    captured = {}

    class DummyResp:
        def __init__(self, data):
            self._data = data
            self.status_code = 200

        def json(self):
            return self._data

        def raise_for_status(self):
            return None


    def fake_post(self, url, json=None, headers=None, timeout=None):
        captured['url'] = url
        captured['json'] = json
        captured['headers'] = headers
        return DummyResp({'ok': True})


    monkeypatch.setattr('requests.Session.post', fake_post, raising=False)

    from src.mcp_adapter.client import ByteroverClient

    client = ByteroverClient(
        endpoint='https://example.test',
        offline_dir=str(tmp_path),
        extension_id='ext-123',
        auth_token='tok-abc',
        max_retries=1,
    )

    res = client.byterover_retrieve_knowledge('q', limit=1)
    assert res == {'ok': True}
    assert 'X-Byterover-Extension' in captured['headers']
    assert captured['headers']['X-Byterover-Extension'] == 'ext-123'
    assert captured['headers']['Authorization'] == 'Bearer tok-abc'


def test_retry_and_offline_on_failed_requests(monkeypatch, tmp_path):
    import requests

    def failing_post(self, url, json=None, headers=None, timeout=None):
        raise requests.exceptions.RequestException("network")

    monkeypatch.setattr('requests.Session.post', failing_post, raising=False)

    from src.mcp_adapter.client import ByteroverClient

    client = ByteroverClient(
        endpoint='https://example.test',
        offline_dir=str(tmp_path),
        extension_id=None,
        auth_token=None,
        max_retries=2,
        backoff_factor=0,
    )

    # Call any wrapper that triggers _post; save implementation plan is convenient
    result = client.byterover_save_implementation_plan({'name': 'plan-x'})

    # On failure the client should write at least one .json file into offline_dir
    files = list(Path(str(tmp_path)).glob('*.json'))
    assert files, f"expected an offline json file in {tmp_path}"

    data = json.loads(files[0].read_text())
    assert 'action' in data and 'payload' in data
