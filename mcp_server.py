"""PrAjeKt MCP 伺服器（Phase 6.5）。

目前工具封裝既有後端 API：
- task_comment_summary(task_id)
- group_snapshot(group_id)
- timeline_generate_tasks(timeline_id)
- timeline_batch_create_tasks(timeline_id, tasks)

weekly_review 會在 Phase 6.4 完成後再接入。
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any
from typing import Optional

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


def _load_local_env() -> None:
    """載入本機 env 檔（若存在）。

    優先級：系統環境變數 > 根目錄 .env.local/.env > backend/.env.local/.env
    這樣可避免執行目錄不同時找不到設定。
    """

    root_dir = Path(__file__).resolve().parent
    candidates = [
        root_dir / ".env.local",
        root_dir / ".env",
        root_dir / "backend" / ".env.local",
        root_dir / "backend" / ".env",
    ]
    for env_file in candidates:
        if env_file.exists():
            load_dotenv(env_file, override=False)


_load_local_env()


class PrAjeKtApiError(RuntimeError):
    """Raised when backend API invocation fails."""


class PrAjeKtApiClient:
    def __init__(self, base_url: str, timeout_sec: float = 30.0) -> None:
        self.base_url = self._normalize_base_url(base_url)
        self.timeout_sec = timeout_sec
        self._session = requests.Session()
        self._token_cache: Optional[str] = None

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        value = (base_url or "http://127.0.0.1:5000/api").strip().rstrip("/")
        if not value.endswith("/api"):
            value = f"{value}/api"
        return value

    def _build_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    @staticmethod
    def _extract_error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
            if isinstance(payload, dict):
                return str(payload.get("error") or payload.get("message") or payload)
            return str(payload)
        except Exception:
            text = (response.text or "").strip()
            return text or f"HTTP {response.status_code}"

    def _resolve_token(self, force_refresh: bool = False) -> str:
        env_token = os.getenv("PRAJEKT_ACCESS_TOKEN", "").strip()
        if env_token:
            return env_token

        if self._token_cache and not force_refresh:
            return self._token_cache

        email = os.getenv("PRAJEKT_EMAIL", "").strip()
        password = os.getenv("PRAJEKT_PASSWORD", "").strip()
        if not email or not password:
            raise PrAjeKtApiError(
                "缺少認證設定。請提供 PRAJEKT_ACCESS_TOKEN，或 PRAJEKT_EMAIL + PRAJEKT_PASSWORD。"
            )

        login_response = self._session.post(
            self._build_url("/auth/login"),
            json={"email": email, "password": password},
            timeout=self.timeout_sec,
        )
        if login_response.status_code != 200:
            message = self._extract_error_message(login_response)
            raise PrAjeKtApiError(f"登入失敗（{login_response.status_code}）：{message}")

        payload = login_response.json() if login_response.content else {}
        token = str(payload.get("access_token") or "").strip()
        if not token:
            raise PrAjeKtApiError("登入成功但 access_token 為空。")

        self._token_cache = token
        return token

    def call_api(
        self,
        method: str,
        path: str,
        *,
        payload: Optional[dict[str, Any]] = None,
        accept_status: Optional[set[int]] = None,
    ) -> tuple[int, dict[str, Any]]:
        expected = accept_status or {200}

        response = self._request_once(method, path, payload)
        if response.status_code in expected:
            return response.status_code, self._to_json(response)

        # 若使用帳密模式，遇到 401 會嘗試重新登入一次。
        if response.status_code == 401 and not os.getenv("PRAJEKT_ACCESS_TOKEN", "").strip():
            self._resolve_token(force_refresh=True)
            response = self._request_once(method, path, payload)
            if response.status_code in expected:
                return response.status_code, self._to_json(response)

        message = self._extract_error_message(response)
        raise PrAjeKtApiError(f"API 呼叫失敗（{response.status_code}）{method.upper()} {path}: {message}")

    def _request_once(self, method: str, path: str, payload: Optional[dict[str, Any]]) -> requests.Response:
        token = self._resolve_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        return self._session.request(
            method=method.upper(),
            url=self._build_url(path),
            headers=headers,
            json=payload,
            timeout=self.timeout_sec,
        )

    @staticmethod
    def _to_json(response: requests.Response) -> dict[str, Any]:
        if not response.content:
            return {}
        data = response.json()
        if isinstance(data, dict):
            return data
        return {"data": data}


mcp = FastMCP("prajekt-phase6")


def _build_client() -> PrAjeKtApiClient:
    base_url = os.getenv("PRAJEKT_API_BASE_URL", "http://127.0.0.1:5000/api")

    token = os.getenv("PRAJEKT_ACCESS_TOKEN", "").strip()
    email = os.getenv("PRAJEKT_EMAIL", "").strip()
    password = os.getenv("PRAJEKT_PASSWORD", "").strip()
    if not token and (not email or not password):
        raise PrAjeKtApiError(
            "缺少認證設定。請在根目錄 .env.local 設定 PRAJEKT_ACCESS_TOKEN，"
            "或同時設定 PRAJEKT_EMAIL 與 PRAJEKT_PASSWORD。"
        )

    timeout_raw = os.getenv("PRAJEKT_TIMEOUT_SEC", "30")
    try:
        timeout_sec = float(timeout_raw)
    except ValueError:
        timeout_sec = 30.0
    return PrAjeKtApiClient(base_url=base_url, timeout_sec=timeout_sec)


@mcp.tool()
def task_comment_summary(task_id: int) -> dict[str, Any]:
    """透過既有 API 產生任務留言摘要。

    Args:
        task_id: PrAjeKt 任務 ID。

    Returns:
        `POST /api/tasks/{task_id}/ai-comment-summary` 的回應 payload。
    """

    if task_id <= 0:
        raise ValueError("task_id 必須是正整數。")

    client = _build_client()
    _, payload = client.call_api(
        "POST",
        f"/tasks/{task_id}/ai-comment-summary",
        payload={},
        accept_status={200},
    )
    return payload


@mcp.tool()
def timeline_generate_tasks(
    timeline_id: int,
    project_name: str = "",
    description: str = "",
) -> dict[str, Any]:
    """透過既有 API 產生專案任務建議。

    Args:
        timeline_id: PrAjeKt 專案 ID。
        project_name: 可選，覆寫專案名稱。
        description: 可選，補充需求描述。

    Returns:
        `POST /api/timelines/{timeline_id}/generate-tasks` 的回應 payload。
    """

    if timeline_id <= 0:
        raise ValueError("timeline_id 必須是正整數。")

    payload: dict[str, Any] = {}
    if isinstance(project_name, str) and project_name.strip():
        payload["name"] = project_name.strip()
    if isinstance(description, str) and description.strip():
        payload["description"] = description.strip()

    client = _build_client()
    _, result = client.call_api(
        "POST",
        f"/timelines/{timeline_id}/generate-tasks",
        payload=payload,
        accept_status={200},
    )
    return result


@mcp.tool()
def timeline_batch_create_tasks(
    timeline_id: int,
    tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    """透過既有 API 批次建立（或保留）專案任務。

    Args:
        timeline_id: PrAjeKt 專案 ID。
        tasks: 任務清單，格式需符合 `batch-create-tasks` API。

    Returns:
        `POST /api/timelines/{timeline_id}/batch-create-tasks` 的回應 payload。
    """

    if timeline_id <= 0:
        raise ValueError("timeline_id 必須是正整數。")
    if not isinstance(tasks, list) or len(tasks) == 0:
        raise ValueError("tasks 必須是非空陣列。")

    client = _build_client()
    _, payload = client.call_api(
        "POST",
        f"/timelines/{timeline_id}/batch-create-tasks",
        payload={"tasks": tasks},
        accept_status={200, 201},
    )
    return payload


@mcp.tool()
def group_snapshot(
    group_id: int,
    window_days: int = 30,
    async_mode: bool = False,
    wait_for_job: bool = True,
    poll_interval_sec: float = 1.5,
    timeout_sec: int = 90,
) -> dict[str, Any]:
    """透過既有 API 產生群組 AI 快照。

    Args:
        group_id: PrAjeKt 群組 ID。
        window_days: 回溯訊息天數。
        async_mode: 是否要求後端改走背景工作。
        wait_for_job: 收到 202 時是否輪詢工作狀態。
        poll_interval_sec: 輪詢間隔（秒）。
        timeout_sec: 最長等待秒數。

    Returns:
        正規化後的回應，包含 sync/async 結果資訊。
    """

    if group_id <= 0:
        raise ValueError("group_id 必須是正整數。")
    if window_days <= 0:
        raise ValueError("window_days 必須是正整數。")
    if poll_interval_sec <= 0:
        raise ValueError("poll_interval_sec 必須大於 0。")
    if timeout_sec <= 0:
        raise ValueError("timeout_sec 必須大於 0。")

    client = _build_client()
    status_code, payload = client.call_api(
        "POST",
        f"/groups/{group_id}/ai-snapshot",
        payload={
            "window_days": int(window_days),
            "async": bool(async_mode),
        },
        accept_status={200, 202},
    )

    if status_code == 200:
        return {
            "mode": "sync",
            "status": "completed",
            "result": payload,
        }

    # 202 代表已排入背景工作
    if not wait_for_job:
        return {
            "mode": "async",
            "status": "queued",
            "job": payload,
        }

    job_id = str(payload.get("job_id") or "").strip()
    if not job_id:
        return {
            "mode": "async",
            "status": "queued",
            "job": payload,
            "warning": "202 回應缺少 job_id，無法輪詢狀態。",
        }

    started = time.time()
    while time.time() - started <= timeout_sec:
        _, job_payload = client.call_api(
            "GET",
            f"/groups/snapshot-jobs/{job_id}",
            accept_status={200},
        )

        job_status = str(job_payload.get("status") or "").lower()
        if job_status == "completed":
            snapshot = job_payload.get("snapshot")
            if isinstance(snapshot, dict):
                return {
                    "mode": "async",
                    "status": "completed",
                    "job": job_payload,
                    "result": snapshot,
                }

            # 若背景工作 payload 未附 snapshot，本地再抓 latest。
            _, latest_payload = client.call_api(
                "GET",
                f"/groups/{group_id}/ai-snapshot/latest",
                accept_status={200},
            )
            return {
                "mode": "async",
                "status": "completed",
                "job": job_payload,
                "result": latest_payload,
            }

        if job_status == "failed":
            message = str(job_payload.get("error") or "群組快照背景工作失敗。")
            raise PrAjeKtApiError(message)

        time.sleep(poll_interval_sec)

    return {
        "mode": "async",
        "status": "timeout",
        "job": payload,
        "message": "背景工作逾時未完成，請稍後改查 latest snapshot。",
    }


if __name__ == "__main__":
    mcp.run()
