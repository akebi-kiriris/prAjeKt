"""PrAjeKt 提示詞管理器

LLM 提示詞配置的集中管理，包括：
- 溫度和 token 上限設定
- 提示詞版本控制
- A/B 測試支援
"""

import os
from datetime import datetime, timezone
from importlib import metadata
from typing import Dict, Any


class PromptManager:
    """管理 LLM 提示詞配置和參數"""

    def __init__(self):
        """依據環境變數初始化提示詞管理器配置"""
        self.temperature_default = float(os.getenv("LLM_TEMPERATURE_DEFAULT", "0.2"))
        self.temperature_creative = float(os.getenv("LLM_TEMPERATURE_CREATIVE", "0.7"))
        self.max_tokens_default = int(os.getenv("LLM_MAX_TOKENS_DEFAULT", "2000"))
        self.max_tokens_long = int(os.getenv("LLM_MAX_TOKENS_LONG", "4000"))

    def get_config(
        self,
        prompt_type: str,
        creative: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        取得特定提示詞類型的 LLM 配置。

        Args:
            prompt_type: 提示詞類型（例如：'summary', 'generation', 'selection'）
            creative: 若為 True，使用更高的溫度以產生更多樣的輸出
            **kwargs: 額外的配置覆蓋

        Returns:
            包含 'temperature'、'max_tokens' 和其他 LLM 參數的字典
        """
        config = {
            "temperature": self.temperature_creative if creative else self.temperature_default,
            "max_tokens": self.max_tokens_long if creative else self.max_tokens_default,
        }

        # 套用特定提示詞類型的覆蓋設定
        if prompt_type == "task_generation":
            config["temperature"] = self.temperature_creative
            config["max_tokens"] = self.max_tokens_long
        elif prompt_type == "tool_selection":
            config["temperature"] = self.temperature_default  # 降低溫度以提高選擇精確度
            config["max_tokens"] = 500  # Small response expected

        # Apply user overrides
        config.update(kwargs)

        return config

    @staticmethod
    def get_version_info() -> Dict[str, str]:
        """取得目前提示詞版本資訊（供稽核與除錯）。"""
        try:
            langchain_version = metadata.version("langchain")
        except metadata.PackageNotFoundError:
            langchain_version = "unknown"

        return {
            "version": "1.0",
            "langchain_version": langchain_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
