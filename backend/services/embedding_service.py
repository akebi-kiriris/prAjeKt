import os
from typing import List

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class EmbeddingOperationError(Exception):
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GeminiEmbeddingService:
    """
    統一的 Embedding 服務，支持多個 LangChain provider。
    透過 EMBEDDING_PROVIDER 環境變數選擇 provider：
    - "google" (預設): Google Generative AI
    - "openai": OpenAI Embeddings
    - "huggingface": HuggingFace Sentence Transformers (本地)
    - "ollama": Ollama (本地)
    """

    def __init__(self, api_key=None, model_name=None, provider=None):
        self.provider = provider or os.getenv("EMBEDDING_PROVIDER", "google").lower()
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
        self._embeddings = None

        if self.provider == "google":
            self._init_google(api_key)
        elif self.provider == "openai":
            self._init_openai(api_key)
        elif self.provider == "huggingface":
            self._init_huggingface()
        elif self.provider == "ollama":
            self._init_ollama()
        else:
            raise EmbeddingOperationError(
                f"不支援的 embedding provider: {self.provider}，請用 google/openai/huggingface/ollama",
                500,
            )

    def _init_google(self, api_key=None):
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError:
            raise EmbeddingOperationError(
                "缺少 langchain-google-genai，請執行 pip install langchain-google-genai",
                500,
            )

        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EmbeddingOperationError("缺少 GOOGLE_API_KEY 環境變數", 500)

        try:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model=self.model_name,
                google_api_key=api_key,
            )
        except Exception as exc:
            raise EmbeddingOperationError(f"Google Embeddings 初始化失敗: {exc}", 500) from exc

    def _init_openai(self, api_key=None):
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            raise EmbeddingOperationError(
                "缺少 langchain-openai，請執行 pip install langchain-openai",
                500,
            )

        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EmbeddingOperationError("缺少 OPENAI_API_KEY 環境變數", 500)

        try:
            self._embeddings = OpenAIEmbeddings(
                model=self.model_name or "text-embedding-3-small",
                api_key=api_key,
            )
        except Exception as exc:
            raise EmbeddingOperationError(f"OpenAI Embeddings 初始化失敗: {exc}", 500) from exc

    def _init_huggingface(self):
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            raise EmbeddingOperationError(
                "缺少 langchain-huggingface，請執行 pip install langchain-huggingface sentence-transformers",
                500,
            )

        try:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name or "sentence-transformers/multilingual-MiniLM-L12-v2"
            )
        except Exception as exc:
            raise EmbeddingOperationError(f"HuggingFace Embeddings 初始化失敗: {exc}", 500) from exc

    def _init_ollama(self):
        try:
            from langchain_ollama import OllamaEmbeddings
        except ImportError:
            raise EmbeddingOperationError(
                "缺少 langchain-ollama，請執行 pip install langchain-ollama",
                500,
            )

        try:
            self._embeddings = OllamaEmbeddings(model=self.model_name or "nomic-embed-text")
        except Exception as exc:
            raise EmbeddingOperationError(f"Ollama Embeddings 初始化失敗: {exc}", 500) from exc

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
    )
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多個文件（用於索引）"""
        if not texts:
            return []

        try:
            return self._embeddings.embed_documents(texts)
        except Exception as exc:
            raise RuntimeError(f"Embedding 失敗: {exc}") from exc

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
    )
    def embed_query(self, text: str) -> List[float]:
        """嵌入查詢文本（用於檢索）"""
        text = (text or "").strip()
        if not text:
            raise EmbeddingOperationError("查詢內容不可為空", 400)

        try:
            return self._embeddings.embed_query(text)
        except Exception as exc:
            raise RuntimeError(f"Embedding 失敗: {exc}") from exc

    def embed_document(self, text: str) -> List[float]:
        """嵌入單個文件（向後相容）"""
        text = (text or "").strip()
        if not text:
            raise EmbeddingOperationError("索引內容不可為空", 400)

        try:
            embeddings = self.embed_documents([text])
            return embeddings[0] if embeddings else []
        except RuntimeError as exc:
            raise EmbeddingOperationError(str(exc), 502) from exc
