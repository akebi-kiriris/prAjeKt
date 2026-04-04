"""AI Provider 抽象層 - 支援多種 AI 模型服務的可替換介面"""

from abc import ABC, abstractmethod
import json
import os
import warnings


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
    """Google Gemini AI Provider"""

    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash-lite"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model

        if not self.api_key:
            raise RuntimeError(
                "Gemini 服務配置不完整：GOOGLE_API_KEY 未設定。"
            )

    def generate_content(self, system_prompt: str, user_message: str, response_format: str = "json") -> str:
        """使用 Gemini 生成內容"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            import google.generativeai as genai

        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)

            # 支援不同的 response 格式
            generation_config = {
                "response_mime_type": "application/json",
                "temperature": 0.2 if response_format == "json" else 0.7,
            }

            response = model.generate_content(
                f"{system_prompt}\n\n{user_message}",
                generation_config=generation_config,
            )
            return response.text
        except Exception as e:
            raise RuntimeError(
                f"Gemini 服務暫時不可用：{str(e)}"
            )


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

