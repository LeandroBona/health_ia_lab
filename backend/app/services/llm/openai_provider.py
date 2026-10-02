import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import GenerationInput, LLMProvider
from .prompt_builder import SYSTEM_PROMPT


class ProviderError(RuntimeError):
    def __init__(self, message: str, code: str = "unavailable"):
        super().__init__(message)
        self.code = code


class OpenAIProvider(LLMProvider):
    """Small Responses API adapter; credentials remain exclusively on the server."""

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 12):
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.timeout = timeout

    def is_available(self) -> bool:
        return bool(self.api_key.strip())

    def get_provider_name(self) -> str:
        return "OpenAI"

    def generate(self, request: GenerationInput) -> str:
        if not self.is_available():
            raise ProviderError("API externa não configurada.", "missing_key")
        payload = {
            "model": self.model,
            "instructions": SYSTEM_PROMPT,
            "input": request.details,
            "max_output_tokens": 300,
            "store": False,
        }
        http_request = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(http_request, timeout=self.timeout) as response:
                body = json.load(response)
        except HTTPError as exc:
            code = {401: "invalid_key", 429: "rate_limit"}.get(exc.code, "model_unavailable" if exc.code in (404, 422) else "server_error")
            raise ProviderError({"invalid_key": "Chave da API inválida.", "rate_limit": "Limite de uso da API atingido.", "model_unavailable": "Modelo externo indisponível.", "server_error": "Serviço externo indisponível."}[code], code) from None
        except (TimeoutError, URLError, OSError):
            raise ProviderError("Tempo limite ou erro de rede na API externa.", "network") from None
        chunks = [piece.get("text", "") for item in body.get("output", []) if item.get("type") == "message" for piece in item.get("content", []) if piece.get("type") == "output_text"]
        result = " ".join(chunks).strip()
        if not result:
            raise ProviderError("A API externa não retornou texto.", "empty")
        return result
