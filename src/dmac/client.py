import json
import logging
import os
import time
from typing import Any, Dict

import requests

_LOGGER = logging.getLogger(__name__)


class DmacClient:
    """Minimal client used in tests.

    Reads the base URL from BYTEROVER_MCP_URL if not provided.
    Writes failed requests to an `offline` directory as a safe fallback.
    """

    def __init__(self, base_url: str | None = None, offline_dir: str | None = None) -> None:
        self.base_url = base_url or os.environ.get("BYTEROVER_MCP_URL", "http://127.0.0.1:8080")
        self.session = requests.Session()
        self.offline_dir = offline_dir or os.path.join(os.getcwd(), "offline")
        os.makedirs(self.offline_dir, exist_ok=True)

    def _post(self, path: str, payload: Dict[str, Any], max_attempts: int = 3, backoff: float = 0.5) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                _LOGGER.debug("POST %s attempt %d/%d", url, attempt, max_attempts)
                resp = self.session.post(url, json=payload, timeout=5)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_exc = exc
                _LOGGER.warning("POST to %s failed (attempt %d): %s", url, attempt, exc)
                time.sleep(backoff * attempt)

        # fallback: write payload to offline dir for later replay
        fname = os.path.join(self.offline_dir, f"failed_{int(time.time())}.json")
        try:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump({"path": path, "payload": payload}, f, indent=2)
            _LOGGER.info("Wrote failed request to %s", fname)
        except Exception as write_exc:
            _LOGGER.error("Failed to write offline payload to %s: %s", fname, write_exc)

        if last_exc is not None:
            raise last_exc
        raise RuntimeError("POST failed and no exception captured")

    def save_implementation_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Save an implementation plan to the MCP endpoint."""
        return self._post("/byterover-save-implementation-plan", {"plan": plan})
