import json
from pathlib import Path

import pytest

from mcp_config import MCPConfigManager


def test_defaults_loaded(tmp_path: Path):
    cfg = MCPConfigManager(config_file=str(tmp_path / "mcp_config.json"))
    # Should load defaults even without a file
    assert cfg.get("mcp_server.url") == "http://localhost:8051/mcp"
    assert isinstance(cfg.get("mcp_server.timeout"), int)


def test_env_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCP_SERVER_URL", "http://example:9999/mcp")
    monkeypatch.setenv("MCP_TIMEOUT", "45")
    cfg = MCPConfigManager(config_file=str(tmp_path / "mcp_config.json"))
    assert cfg.get("mcp_server.url") == "http://example:9999/mcp"
    assert cfg.get("mcp_server.timeout") == 45


def test_get_set_roundtrip(tmp_path: Path):
    cfg = MCPConfigManager(config_file=str(tmp_path / "mcp_config.json"))
    cfg.set("logging.level", "DEBUG")
    assert cfg.get("logging.level") == "DEBUG"


def test_validate(tmp_path: Path):
    cfg = MCPConfigManager(config_file=str(tmp_path / "mcp_config.json"))
    ok, issues = cfg.validate_config()
    assert ok, f"unexpected validation issues: {issues}"


def test_generate_default_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_path = tmp_path / "mcp_config.json"
    cfg = MCPConfigManager(config_file=str(cfg_path))
    # First generate should succeed without prompt
    assert cfg.generate_default_config(force=True)
    assert cfg_path.exists()
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert "mcp_server" in data

