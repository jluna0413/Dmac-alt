import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class ByteroverClient:
    """Thin client for Byterover MCP with an offline fallback.

    Usage:
        client = ByteroverClient(endpoint=None, offline_dir='byterover_offline')
        client.byterover_save_implementation_plan({ 'title': 'Plan' })

    Behavior notes:
    - If `endpoint` is None the client writes JSON records to `offline_dir`.
    - When `extension_id` is provided the header `X-Byterover-Extension` is sent on remote calls.
    - When `auth_token` is provided the header `Authorization: Bearer <token>` is sent on remote calls.
    - The client implements a small manual retry/backoff loop (configurable via `max_retries` and
      `backoff_factor`) so unit tests that mock `Session.post` still exercise retry semantics.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        offline_dir: str = ".byterover_offline",
        extension_id: Optional[str] = None,
        auth_token: Optional[str] = None,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ):
        self.endpoint = endpoint
        self.offline_dir = Path(offline_dir)
        self.extension_id = extension_id
        self.auth_token = auth_token
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self.session = requests.sessions.Session()
        try:
            from urllib3.util.retry import Retry
            from requests.adapters import HTTPAdapter

            retry_strategy = Retry(total=max_retries, backoff_factor=backoff_factor, status_forcelist=[429, 500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
        except (ImportError, AttributeError, ValueError):
            pass

        if not self.offline_dir.exists():
            self.offline_dir.mkdir(parents=True, exist_ok=True)

    def _write_offline(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")
        filename = self.offline_dir / f"{ts}_{action}.json"
        record = {"action": action, "payload": payload, "saved_at": datetime.utcnow().isoformat()}
        with open(filename, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2)
        logger.info("Wrote offline byterover record: %s", filename)
        return {"success": True, "offline_file": str(filename)}

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.endpoint:
            return self._write_offline(path, payload)
        url = f"{self.endpoint.rstrip('/')}/{path.lstrip('/')}"
        headers: Dict[str, str] = {}
        if self.extension_id:
            headers["X-Byterover-Extension"] = self.extension_id
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                r = self.session.post(url, json=payload, timeout=10, headers=headers)
                r.raise_for_status()
                return r.json()
            except (requests.RequestException, ValueError, KeyError) as e:
                last_exc = e
                logger.warning("Byterover call failed (attempt %d/%d) for %s: %s", attempt + 1, self.max_retries, path, e)
                logger.debug("Byterover retry details: attempt=%d path=%s exception=%s", attempt + 1, path, repr(e))
                if attempt < self.max_retries - 1:
                    sleep_for = self.backoff_factor * (2 ** attempt)
                    time.sleep(sleep_for)
                    continue
                logger.warning("Byterover call exhausted retries, falling back to offline: %s", last_exc)
                return self._write_offline(path, payload)

        logger.warning("Byterover call unexpected exit path, falling back to offline: %s", path)
        return self._write_offline(path, payload)

    def byterover_check_handbook_existence(self) -> Dict[str, Any]:
        return self._post("byterover-check-handbook-existence", {})

    def byterover_save_implementation_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"plan": plan}
        return self._post("byterover-save-implementation-plan", payload)

    def byterover_update_plan_progress(self, project_id: str, task_name: Optional[str] = None, is_completed: bool = False) -> Dict[str, Any]:
        payload = {"project_id": project_id, "task_name": task_name, "is_completed": is_completed}
        return self._post("byterover-update-plan-progress", payload)

    def byterover_store_knowledge(self, messages: str) -> Dict[str, Any]:
        payload = {"messages": messages}
        return self._post("byterover-store-knowledge", payload)

    def byterover_retrieve_knowledge(self, query: str, limit: int = 3) -> Dict[str, Any]:
        if not self.endpoint:
            return {"success": False, "error": "offline", "results": []}
        return self._post("byterover-retrieve-knowledge", {"query": query, "limit": limit})

    def byterover_create_project(self, title: str, description: Optional[str] = None) -> Dict[str, Any]:
        payload = {"title": title, "description": description}
        return self._post("byterover-create-project", payload)

    def byterover_create_task(self, project_id: str, title: str, description: Optional[str] = None, assignee: Optional[str] = None, task_order: Optional[int] = None) -> Dict[str, Any]:
        payload = {"project_id": project_id, "title": title, "description": description, "assignee": assignee, "task_order": task_order}
        return self._post("byterover-create-task", payload)

    def byterover_retrieve_active_plans(self) -> Dict[str, Any]:
        # This method retrieves active plans from Byterover.
        return self._post("byterover-retrieve-active-plans", {})
