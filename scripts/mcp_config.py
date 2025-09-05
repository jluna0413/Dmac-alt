#!/usr/bin/env python3
"""
MCP Test Configuration Management Utility

Centralized configuration management for all MCP test scripts.

Features:
- Centralized configuration validation
- Environment variable overrides
- Configuration file support (JSON)
- Runtime get/set helpers (dot notation)
- Connectivity test helper

Usage (examples):
  python mcp_config.py validate
  python mcp_config.py show
  python mcp_config.py set mcp_server.url http://new-server:8051/mcp
  python mcp_config.py generate-config
  python mcp_config.py test-connection

With a custom config file:
    python mcp_config.py --config A:\\Projects\\my_config.json show
    python mcp_config.py -c ./alt_config.json validate
"""

import argparse
import copy
import json
import locale
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


class MCPConfigManager:
    """Manage MCP test configuration: load, validate, override, and persist."""

    def __init__(self, config_file: Optional[str] = None) -> None:
        self.config_file = Path(config_file or "mcp_config.json")
        self.config: Dict[str, Any] = {}

        self.default_config: Dict[str, Any] = {
            "mcp_server": {
                "url": "http://localhost:8051/mcp",
                "timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 1.0,
            },
            "test_settings": {
                "verbose_mode": False,
                "save_results": True,
                "result_directory": "test_results",
                "max_execution_time": 300,
            },
            "protocol": {
                "version": "2024-11-05",
                "client_name": "MCP-Test-Suite",
                "client_version": "1.0.0",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {},
                },
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_logging": False,
                "log_file": "mcp_tests.log",
            },
        }

        self.load_config()

    # ----- icons/printing -------------------------------------------------
    @staticmethod
    def _icons() -> Dict[str, str]:
        enc_raw: str = str(
            sys.stdout.encoding or locale.getpreferredencoding(False) or ""
        )
        enc = enc_raw.lower()
        if "utf" in enc:
            return {
                "ok": "✅",
                "warn": "⚠️",
                "err": "❌",
                "link": "🔗",
                "clip": "📋",
                "doc": "📄",
            }
        return {
            "ok": "[OK]",
            "warn": "[!]",
            "err": "[X]",
            "link": "[->]",
            "clip": "[CFG]",
            "doc": "[DOC]",
        }

    # ----- load/merge/env -------------------------------------------------
    def load_config(self) -> None:
        """Load defaults, merge file if present, then apply env overrides."""
        self.config = copy.deepcopy(self.default_config)

        if self.config_file.exists():
            try:
                with self.config_file.open("r", encoding="utf-8") as f:
                    file_cfg = json.load(f)
                self._merge_config(self.config, file_cfg)
                icons = self._icons()
                print(f"{icons['ok']} Configuration loaded from {self.config_file}")
            except (OSError, json.JSONDecodeError) as e:
                icons = self._icons()
                print(f"{icons['warn']} Error loading config file: {e}")

        self._load_env_overrides()

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        for k, v in override.items():
            if isinstance(base.get(k), dict) and isinstance(v, dict):
                self._merge_config(base[k], v)
            else:
                base[k] = v

    def _load_env_overrides(self) -> None:
        env_map = {
            "MCP_SERVER_URL": ("mcp_server", "url"),
            "MCP_TIMEOUT": ("mcp_server", "timeout"),
            "MCP_RETRY_ATTEMPTS": ("mcp_server", "retry_attempts"),
            "MCP_RETRY_DELAY": ("mcp_server", "retry_delay"),
            "DEBUG_VERBOSE": ("test_settings", "verbose_mode"),
            "LOG_LEVEL": ("logging", "level"),
            "TEST_RESULTS_DIR": ("test_settings", "result_directory"),
        }

        for env_var, (section, key) in env_map.items():
            raw = os.getenv(env_var)
            if raw is None:
                continue

            value: Any = raw
            if key in {"timeout", "retry_attempts", "max_execution_time"}:
                try:
                    value = int(raw)
                except ValueError:
                    print(f"⚠️ Invalid integer for {env_var}: {raw}")
                    continue
            elif key in {"retry_delay"}:
                try:
                    value = float(raw)
                except ValueError:
                    print(f"⚠️ Invalid float for {env_var}: {raw}")
                    continue
            elif key in {"verbose_mode", "save_results", "file_logging"}:
                value = raw.lower() in {"true", "1", "yes", "on"}

            if section not in self.config or not isinstance(self.config[section], dict):
                self.config[section] = {}
            self.config[section][key] = value

    # ----- validation -----------------------------------------------------
    def validate_config(self) -> Tuple[bool, List[str]]:
        issues: List[str] = []
        issues.extend(self._validate_server_config())
        issues.extend(self._validate_protocol_config())
        issues.extend(self._validate_directories())
        return (len(issues) == 0, issues)

    def _validate_server_config(self) -> List[str]:
        issues: List[str] = []
        url = self.get("mcp_server.url")
        timeout = self.get("mcp_server.timeout")

        if not url or not isinstance(url, str):
            issues.append("MCP server URL is required")
        if timeout is None or not isinstance(timeout, int) or timeout <= 0:
            issues.append("Timeout must be a positive integer")
        return issues

    def _validate_protocol_config(self) -> List[str]:
        issues: List[str] = []
        version = self.get("protocol.version")
        if not version or not isinstance(version, str):
            issues.append("Protocol version is required")
        return issues

    def _validate_directories(self) -> List[str]:
        issues: List[str] = []
        result_dir = self.get("test_settings.result_directory")
        if result_dir:
            try:
                Path(result_dir).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                issues.append(f"Cannot create result directory '{result_dir}': {e}")
        return issues

    # ----- accessors ------------------------------------------------------
    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")
        value: Any = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        keys = key_path.split(".")
        ref = self.config
        for key in keys[:-1]:
            if key not in ref or not isinstance(ref[key], dict):
                ref[key] = {}
            ref = ref[key]
        ref[keys[-1]] = value

    def save_config(self) -> bool:
        try:
            with self.config_file.open("w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            icons = self._icons()
            print(f"{icons['ok']} Configuration saved to {self.config_file}")
            return True
        except OSError as e:
            icons = self._icons()
            print(f"{icons['err']} Failed to save configuration: {e}")
            return False

    def generate_default_config(self, *, force: bool = False) -> bool:
        if self.config_file.exists() and not force:
            resp = input(f"Config file {self.config_file} exists. Overwrite? (y/N): ")
            if resp.strip().lower() != "y":
                print("Configuration generation cancelled.")
                return False
        try:
            with self.config_file.open("w", encoding="utf-8") as f:
                json.dump(self.default_config, f, indent=2)
            icons = self._icons()
            print(f"{icons['ok']} Default configuration generated: {self.config_file}")
            return True
        except OSError as e:
            icons = self._icons()
            print(f"{icons['err']} Failed to generate configuration: {e}")
            return False

    def test_connection(self) -> bool:
        url = self.get("mcp_server.url")
        timeout = self.get("mcp_server.timeout", 30)
        attempts = max(1, int(self.get("mcp_server.retry_attempts", 1)))
        delay = float(self.get("mcp_server.retry_delay", 1.0) or 0)
        icons = self._icons()
        print(
            f"{icons['link']} Testing connection to {url} (attempts={attempts}, delay={delay}s)"
        )

        base_url = url.replace("/mcp", "") if url else url
        for i in range(1, attempts + 1):
            try:
                resp = requests.get(base_url, timeout=timeout)
                print(
                    f"{icons['ok']} Base endpoint reachable - HTTP {resp.status_code}"
                )

                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": "config-test",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": self.get("protocol.version"),
                        "capabilities": self.get("protocol.capabilities"),
                        "clientInfo": {
                            "name": self.get("protocol.client_name"),
                            "version": self.get("protocol.client_version"),
                        },
                    },
                }
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                }
                mcp_resp = requests.post(
                    url, json=mcp_request, headers=headers, timeout=timeout
                )
                if mcp_resp.status_code == 200:
                    print(
                        f"{icons['ok']} MCP protocol response - HTTP {mcp_resp.status_code}"
                    )
                    return True
                warn_left = attempts - i
                print(
                    f"{icons['warn']} MCP endpoint returned HTTP {mcp_resp.status_code} (retries left: {warn_left})"
                )
            except requests.RequestException as e:
                warn_left = attempts - i
                print(
                    f"{icons['warn']} Connection error: {e} (retries left: {warn_left})"
                )

            if i < attempts and delay > 0:
                time.sleep(delay)

        print(f"{icons['err']} Connection test failed after {attempts} attempt(s)")
        return False

    def show_config(self) -> None:
        icons = self._icons()
        print(f"{icons['clip']} CURRENT MCP TEST CONFIGURATION")
        print("=" * 50)

        def print_section(data: Dict[str, Any], prefix: str = "") -> None:
            for k, v in data.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    print(f"\n[{full_key.upper()}]")
                    print_section(v, full_key)
                else:
                    print(f"  {k}: {v}")

        print_section(self.config)

        print(f"\n{icons['doc']} Configuration sources:")
        print(
            f"  • Config file: {self.config_file} ({'exists' if self.config_file.exists() else 'not found'})"
        )
        print("  • Environment variables: Applied")


# ----- CLI ---------------------------------------------------------------


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MCP Test Configuration Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Global options
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        help="Path to configuration file (defaults to mcp_config.json in CWD)",
        default=None,
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    sub.add_parser("validate", help="Validate current configuration")
    sub.add_parser("show", help="Show current configuration")

    set_cmd = sub.add_parser("set", help="Set configuration value")
    set_cmd.add_argument("key", help="Configuration key (dot notation)")
    set_cmd.add_argument("value", help="Configuration value")

    gen = sub.add_parser("generate-config", help="Generate default configuration file")
    gen.add_argument(
        "--force", "-f", action="store_true", help="Overwrite without prompt"
    )

    sub.add_parser("test-connection", help="Test connectivity to MCP server")
    return parser


def _execute_command(cfg: MCPConfigManager, args: argparse.Namespace) -> int:
    if args.command == "validate":
        ok, issues = cfg.validate_config()
        if ok:
            print("✅ Configuration is valid")
            return 0
        print("❌ Configuration validation failed:")
        for i in issues:
            print(f"  • {i}")
        return 1
    if args.command == "show":
        cfg.show_config()
        return 0
    if args.command == "set":
        val = _convert_value_for_key(args.key, args.value)
        if val is None and args.value is not None:
            return 1
        cfg.set(args.key, val)
        cfg.save_config()
        print(f"✅ Set {args.key} = {val}")
        return 0
    if args.command == "generate-config":
        ok = cfg.generate_default_config(force=getattr(args, "force", False))
        return 0 if ok else 1
    if args.command == "test-connection":
        ok = cfg.test_connection()
        return 0 if ok else 1
    print(f"❌ Unknown command: {args.command}")
    return 1


def _convert_value_for_key(key: str, value: str) -> Any:
    if key.endswith(("timeout", "retry_attempts", "max_execution_time")):
        try:
            return int(value)
        except ValueError:
            print(f"❌ Invalid integer value: {value}")
            return None
    if key.endswith("retry_delay"):
        try:
            return float(value)
        except ValueError:
            print(f"❌ Invalid float value: {value}")
            return None
    if key.endswith(("verbose_mode", "save_results", "file_logging")):
        return value.lower() in {"true", "1", "yes", "on"}
    return value


def main() -> int:
    parser = _create_argument_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        cfg = MCPConfigManager(config_file=args.config)
        return _execute_command(cfg, args)
    except KeyboardInterrupt:
        print("\n⚠️ Configuration management interrupted")
        return 1
    except (ValueError, OSError, RuntimeError) as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
