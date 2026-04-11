"""AI Provider 抽象層 - 支援多種 AI 模型服務的可替換介面"""

from abc import ABC, abstractmethod
import json
import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from chains.llm_factory import get_default_llm


class AIProvider(ABC):
    """AI Provider 基類 - 定義所有 AI 服務的共同介面"""

    @abstractmethod
    def generate_content(self, system_prompt: str, user_message: str, response_format: str = "json") -> str:
        """
        生成內容 - 支援多種格式

        Args:
            system_prompt: 系統提示詞（包含指令）
            user_message: 用戶訊息（業務內容）
            response_format: 回應格式 - "json" 或 "json_array"（預設 "json"）

        Returns:
            str: 根據格式回傳的結果（JSON 物件或 JSON 陣列）

        Raises:
            RuntimeError: 服務連線或處理失敗
        """
        pass


class GeminiProvider(AIProvider):
    """Google Gemini AI Provider - 使用 LangChain"""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        # 優先使用 AI_MODEL 環境變數，或傳入的 model 參數，最後回退預設值
        if model is None:
            model = os.getenv("AI_MODEL") or "gemini-2.5-flash-lite"
        self.model = model

        if not self.api_key:
            raise RuntimeError(
                "Gemini 服務配置不完整：GOOGLE_API_KEY 未設定。"
            )

        try:
            self.llm = get_default_llm(
                provider="google-generativeai",
                api_key=self.api_key,
                model_name=self.model,
                temperature=float(os.getenv("LLM_TEMPERATURE_DEFAULT", "0.2")),
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini 服務初始化失敗：{str(exc)}") from exc

    @staticmethod
    def _to_text(response: Any) -> str:
        content = getattr(response, "content", response)

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "\n".join(part for part in parts if part).strip()

        return str(content or "").strip()

    def generate_content(self, system_prompt: str, user_message: str, response_format: str = "json") -> str:
        """使用 LangChain 生成內容並回傳文字（由呼叫端解析 JSON）"""

        format_hint = (
            "請只輸出 JSON 陣列，不要附加說明文字。"
            if response_format == "json_array"
            else "請只輸出 JSON 物件，不要附加說明文字。"
        )

        final_system_prompt = f"{system_prompt}\n\n{format_hint}"

        try:
            response = self.llm.invoke(
                [
                    SystemMessage(content=final_system_prompt),
                    HumanMessage(content=user_message),
                ]
            )

            result = self._to_text(response)
            if not result:
                raise RuntimeError("Gemini 回應為空")
            return result
        except Exception as e:
            error_msg = str(e)
            if "API_KEY" in error_msg or "api_key" in error_msg.lower():
                raise RuntimeError(f"Gemini 服務配置不完整：{error_msg}") from e
            raise RuntimeError(f"Gemini 服務暫時不可用：{error_msg}") from e


class MockProvider(AIProvider):
    """Mock AI Provider - 用於測試與開發環境"""

    def __init__(self):
        pass

    def generate_content(self, system_prompt: str, user_message: str, response_format: str = "json") -> str:
        """回傳模擬的結果"""
        if response_format == "json_array":
            return json.dumps([
                {
                    "name": "Mock 任務 1",
                    "priority": 1,
                    "estimated_days": 3,
                    "task_remark": "Mock 備註"
                },
                {
                    "name": "Mock 任務 2",
                    "priority": 2,
                    "estimated_days": 5,
                    "task_remark": "Mock 備註 2"
                }
            ])
        else:
            # 預設 JSON 物件格式
            return json.dumps({
                "decisions": ["Mock 決議 1", "Mock 決議 2"],
                "risks": ["Mock 風險 1"],
                "next_actions": ["Mock 下一步 1", "Mock 下一步 2"]
            })


def get_ai_provider() -> AIProvider:
    """
    工廠函數 - 根據環境變數返回對應的 AI Provider

    環境變數 AI_PROVIDER 可選值：
    - "gemini"（預設）：使用 Google Gemini
    - "mock"：使用 Mock Provider（開發/測試用）
    - 其他值：回退到 Gemini

    Returns:
        AIProvider: 根據環境配置選定的 AI 服務實例

    Raises:
        RuntimeError: Provider 配置失敗時
    """
    provider_name = os.getenv("AI_PROVIDER", "gemini").lower()
    # 從環境變數讀取要使用的模型型號（可透過 AI_MODEL 指定）
    model = os.getenv("AI_MODEL", "gemini-2.5-flash-lite")

    if provider_name == "mock":
        return MockProvider()
    else:
        # 預設或其他所有提供者目前皆使用 GeminiProvider，可傳入 model
        return GeminiProvider(model=model)

