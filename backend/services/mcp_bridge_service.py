import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any


class MCPBridgeError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class _MCPSubprocessClient:
    def __init__(self, env_overrides: dict[str, str] | None = None, timeout_sec: float = 30.0):
        self.env_overrides = env_overrides or {}
        self.timeout_sec = timeout_sec
        self._request_id = 0
        self._process: subprocess.Popen[str] | None = None

    def __enter__(self):
        self._start_process()
        self._initialize()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._shutdown()

    def _start_process(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        server_script = Path(os.getenv("MCP_SERVER_SCRIPT", str(project_root / "mcp_server.py"))).resolve()
        python_exec = os.getenv("MCP_SERVER_PYTHON", sys.executable)

        if not server_script.exists():
            raise MCPBridgeError(f"找不到 MCP Server 檔案：{server_script}", 500)

        env = os.environ.copy()
        env.update(self.env_overrides)

        try:
            self._process = subprocess.Popen(
                [python_exec, str(server_script)],
                cwd=str(project_root),
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            raise MCPBridgeError(f"啟動 MCP Server 失敗：{exc}", 500) from exc

    def _shutdown(self) -> None:
        if self._process is None:
            return

        try:
            if self._process.poll() is None:
                self._process.terminate()
                self._process.wait(timeout=2)
        except Exception:
            try:
                self._process.kill()
            except Exception:
                pass

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _readline_with_timeout(self) -> str:
        if self._process is None or self._process.stdout is None:
            raise MCPBridgeError("MCP Server 尚未啟動", 500)

        output_box: dict[str, str] = {}
        error_box: dict[str, Exception] = {}

        def _reader():
            try:
                output_box["line"] = self._process.stdout.readline()
            except Exception as exc:
                error_box["error"] = exc

        thread = threading.Thread(target=_reader, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout_sec)

        if thread.is_alive():
            raise MCPBridgeError("等待 MCP 回應逾時", 504)

        if "error" in error_box:
            raise MCPBridgeError(f"讀取 MCP 回應失敗：{error_box['error']}", 500)

        line = output_box.get("line", "")
        if line:
            return line

        if self._process.poll() is not None:
            stderr_text = ""
            if self._process.stderr is not None:
                try:
                    stderr_text = (self._process.stderr.read() or "").strip()
                except Exception:
                    stderr_text = ""
            detail = f"；stderr={stderr_text}" if stderr_text else ""
            raise MCPBridgeError(f"MCP Server 已結束且未回傳資料{detail}", 500)

        raise MCPBridgeError("MCP Server 未回傳可解析資料", 500)

    def _send_rpc(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._process is None or self._process.stdin is None:
            raise MCPBridgeError("MCP Server 尚未啟動", 500)

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {},
        }

        try:
            self._process.stdin.write(json.dumps(payload) + "\n")
            self._process.stdin.flush()
        except Exception as exc:
            raise MCPBridgeError(f"傳送 MCP 請求失敗：{exc}", 500) from exc

        response: dict[str, Any] | None = None
        last_non_json_line = ""
        for _ in range(8):
            line = self._readline_with_timeout().strip()
            if not line:
                continue

            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                last_non_json_line = line
                continue

            if isinstance(parsed, dict):
                response = parsed
                break

        if response is None:
            if last_non_json_line:
                raise MCPBridgeError(f"MCP 回應非 JSON：{last_non_json_line[:200]}", 500)
            raise MCPBridgeError("MCP 回應為空或格式錯誤", 500)

        if "error" in response:
            error_payload = response.get("error")
            message = error_payload.get("message") if isinstance(error_payload, dict) else str(error_payload)
            raise MCPBridgeError(f"MCP 工具呼叫失敗：{message}", 400)

        result = response.get("result")
        if not isinstance(result, dict):
            return {}
        return result

    def _initialize(self) -> None:
        self._send_rpc(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "prajekt-backend-copilot",
                    "version": "1.0.0",
                },
            },
        )

    def list_tools(self) -> list[dict[str, Any]]:
        result = self._send_rpc("tools/list", {})
        tools = result.get("tools", [])
        if isinstance(tools, list):
            return [tool for tool in tools if isinstance(tool, dict)]
        return []

    def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._send_rpc(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments or {},
            },
        )


def _extract_structured_result(raw_result: dict[str, Any]) -> Any:
    structured = raw_result.get("structuredContent")
    if structured is not None:
        return structured

    content = raw_result.get("content")
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_value = item.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    text_parts.append(text_value.strip())

        if text_parts:
            merged = "\n".join(text_parts)
            try:
                return json.loads(merged)
            except json.JSONDecodeError:
                return {"raw_text": merged}

    return raw_result


def _build_env_overrides(access_token: str | None = None) -> dict[str, str]:
    env: dict[str, str] = {}
    if isinstance(access_token, str) and access_token.strip():
        env["PRAJEKT_ACCESS_TOKEN"] = access_token.strip()
    return env


def list_mcp_tools(access_token: str | None = None) -> list[dict[str, Any]]:
    env_overrides = _build_env_overrides(access_token)
    with _MCPSubprocessClient(env_overrides=env_overrides) as client:
        return client.list_tools()


def execute_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    env_overrides = _build_env_overrides(access_token)
    with _MCPSubprocessClient(env_overrides=env_overrides) as client:
        tools = client.list_tools()
        tool_names = {str(tool.get("name") or "") for tool in tools}
        if tool_name not in tool_names:
            raise MCPBridgeError(f"找不到工具：{tool_name}", 400)

        raw_result = client.call_tool(tool_name, arguments or {})
        parsed_result = _extract_structured_result(raw_result)

    return {
        "tool_name": tool_name,
        "raw_result": raw_result,
        "parsed_result": parsed_result,
        "available_tools": tools,
    }
