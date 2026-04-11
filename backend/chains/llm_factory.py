"""LLM 工廠函式

LangChain LLM 實例初始化的工廠函式。
封裝 LLM 配置和初始化邏輯。
"""

import os
from typing import Callable, Optional
from langchain_core.language_models.chat_models import BaseChatModel


DEFAULT_PROVIDER = "google-generativeai"

# 將輸入別名歸一化，後續新增提供者時只需補這裡與工廠映射。
PROVIDER_ALIASES = {
    "google-generativeai": "google-generativeai",
    "google": "google-generativeai",
    "gemini": "google-generativeai",
}


def create_google_generative_ai(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> BaseChatModel:
    """
    為 LangChain 建立 Google Generative AI LLM 實例。

    Args:
        api_key: Google API 金鑰（預設從 GOOGLE_API_KEY 環境變數取得）
        model_name: 模型名稱（預設從 AI_MODEL 環境變數取得，最後預設為 gemini-2.5-flash-lite）
        temperature: LLM 溫度（0-1）
        max_tokens: 最大輸出 token 數

    Returns:
        GoogleGenerativeAI LLM 實例
    """
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY 環境變數未設定且未提供 api_key"
            )

    # 若未指定模型名稱，從環境變數取得
    if model_name is None:
        model_name = os.getenv("AI_MODEL") or "gemini-2.5-flash-lite"

    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        google_api_key=api_key,
        model=model_name,
        temperature=temperature,
        max_output_tokens=max_tokens or 2048,
    )

    return llm


PROVIDER_FACTORIES: dict[str, Callable[..., BaseChatModel]] = {
    "google-generativeai": create_google_generative_ai,
}


def _normalize_provider(provider: str) -> str:
    normalized = (provider or "").strip().lower()
    if not normalized:
        return DEFAULT_PROVIDER
    return PROVIDER_ALIASES.get(normalized, normalized)


def get_default_llm(
    provider: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """
    根據環境配置取得預設的 LLM 實例。

    Args:
        provider: LLM 提供者名稱（可由環境變數 LLM_PROVIDER 指定）
        **kwargs: LLM 的額外配置

    Returns:
        已配置的 LLM 實例

    Raises:
        ValueError: 若提供者不支援或必要的環境變數未設定
    """
    # 若未指定 provider，從環境變數取得
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER)

    normalized = _normalize_provider(provider)
    factory = PROVIDER_FACTORIES.get(normalized)

    if factory is None:
        available = ", ".join(sorted(PROVIDER_FACTORIES.keys()))
        raise ValueError(
            f"不支援的 LLM 提供者: {provider}。目前可用提供者: {available}。"
        )

    return factory(**kwargs)
