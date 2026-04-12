from __future__ import annotations

import json
import urllib.parse
import urllib.request
import urllib.error

BASE_URL = "https://timecrowd.net/api/v1"


class TimeCrowdAPI:
    def __init__(self, token: str):
        self.token = token

    def _request(self, method: str, path: str, data: dict | None = None) -> dict | list:
        url = f"{BASE_URL}{path}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status == 204:
                    return {}
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"API Error {e.code}: {error_body}") from e

    def get_user(self) -> dict:
        return self._request("GET", "/user")

    def get_teams(self) -> list:
        return self._request("GET", "/teams")

    def get_categories(self, team_id: str) -> list:
        tid = urllib.parse.quote(str(team_id), safe="")
        return self._request("GET", f"/categories?team_id={tid}")

    def get_tasks(self, sort: str = "user_usage", limit: int = 25) -> dict:
        return self._request("GET", f"/tasks?sort={sort}&limit={limit}")

    def search_tasks(self, query: str) -> list:
        encoded = urllib.parse.quote(query)
        return self._request("GET", f"/search/tasks?q={encoded}")

    def start_task(self, team_id: str, task_id: str) -> dict:
        tid = urllib.parse.quote(str(team_id), safe="")
        tkid = urllib.parse.quote(str(task_id), safe="")
        return self._request("POST", f"/teams/{tid}/tasks/{tkid}/start", {})

    def stop_entry(self, entry_id: str) -> dict:
        eid = urllib.parse.quote(str(entry_id), safe="")
        return self._request("PATCH", f"/time_entries/{eid}/stop")

    def get_time_entries(self, **params) -> list:
        query = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items())
        path = f"/time_entries?{query}" if query else "/time_entries"
        return self._request("GET", path)

    def get_active_entry(self) -> dict | None:
        """v2 API でユーザーの打刻中エントリを取得"""
        url = "https://timecrowd.net/api/v2/user"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                entry = data.get("time_entry")
                if entry and entry.get("stopped_at") is None:
                    return entry
        except Exception:
            pass
        return None

    def delete_entry(self, entry_id: str) -> dict:
        eid = urllib.parse.quote(str(entry_id), safe="")
        return self._request("DELETE", f"/time_entries/{eid}")
