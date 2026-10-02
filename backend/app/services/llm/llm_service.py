import logging
import os
import re
from datetime import datetime, timezone

from .base import GenerationInput
from .local_provider import LocalTemplateProvider
from .openai_provider import OpenAIProvider, ProviderError
from .prompt_builder import build_explanation_prompt, detail_sentence, fact_sentence
from .schemas import ContentRequest, ExplainRequest, QuestionRequest, minimize

logger = logging.getLogger(__name__)
UNSAFE = re.compile(r"\b(diagn[oó]stic[oa]|tratamento|transtorno|prescri[cç][aã]o|urgente|risco cl[ií]nico)\b", re.I)


class LLMService:
    def __init__(self, external: OpenAIProvider | None = None, local: LocalTemplateProvider | None = None):
        self.external = external or OpenAIProvider()
        self.local = local or LocalTemplateProvider()

    def status(self) -> dict:
        online = self.external.is_available()
        return {"provider": self.external.get_provider_name() if online else self.local.get_provider_name(),
                "available": True, "model": self.external.model if online else None,
                "mode": "online" if online else "offline"}

    @staticmethod
    def _response(provider: str, explanation: str, mode: str, fallback_reason: str | None = None) -> dict:
        return {"provider": provider, "explanation": explanation, "generated_at": datetime.now(timezone.utc).isoformat(),
                "mode": mode, "fallback_reason": fallback_reason}

    def explain(self, request: ExplainRequest) -> dict:
        data = minimize(request)
        facts = fact_sentence(request.module, request.analysis_type, data)
        details = detail_sentence(request.analysis_type, data)
        local_input = GenerationInput(task="explain", module=request.module, analysis_type=request.analysis_type,
                                      level=request.level, facts=facts, details=details)
        if request.provider == "local" or not self.external.is_available():
            response = self._response(self.local.get_provider_name(), self.local.generate(local_input), "offline")
            logger.info("generative_explain provider=local module=%s type=%s success=true", request.module, request.analysis_type)
            return response
        prompt = build_explanation_prompt(request.module, request.analysis_type, request.level, facts, data)
        try:
            addition = self.external.generate(GenerationInput(task="explain", details=prompt, creativity="Baixa"))
            # Numbers and model results are rendered only by deterministic code. Reject unsafe additions.
            if re.search(r"\d", addition) or UNSAFE.search(addition) or len(addition) > 1000:
                raise ProviderError("A resposta externa não passou na validação de fidelidade.", "invalid_output")
            logger.info("generative_explain provider=openai module=%s type=%s success=true", request.module, request.analysis_type)
            return self._response(self.external.get_provider_name(), f"{facts}\n\n{addition.strip()}\n\n{details}", "online")
        except ProviderError as exc:
            logger.warning("generative_explain provider=openai module=%s type=%s success=false code=%s", request.module, request.analysis_type, exc.code)
            return self._response(self.local.get_provider_name(), self.local.generate(local_input), "offline", exc.code)

    def educational(self, request: ContentRequest) -> dict:
        local_input = GenerationInput(task="content", topic=request.topic, level=request.level,
                                      length=request.length, creativity=request.creativity)
        if not self.external.is_available():
            return self._response(self.local.get_provider_name(), self.local.generate(local_input), "offline")
        try:
            details = f"Explique didaticamente {request.topic}. Nível: {request.level}. Tamanho: {request.length}. Use apenas exemplos sintéticos. Não faça interpretação clínica."
            output = self.external.generate(GenerationInput(task="content", details=details, creativity=request.creativity))
            if UNSAFE.search(output):
                raise ProviderError("Conteúdo inadequado para o laboratório.", "invalid_output")
            return self._response(self.external.get_provider_name(), output, "online")
        except ProviderError as exc:
            return self._response(self.local.get_provider_name(), self.local.generate(local_input), "offline", exc.code)

    def question(self, request: QuestionRequest) -> dict:
        local_input = GenerationInput(task="question", topic=request.topic)
        if not self.external.is_available():
            return self._response(self.local.get_provider_name(), self.local.generate(local_input), "offline")
        try:
            details = f"Crie uma pergunta curta para discussão acadêmica sobre IA e {request.topic}. Resultado sintético: {request.result}. A pergunta deve tratar de dados, modelos, estatística, ética ou limitações."
            output = self.external.generate(GenerationInput(task="question", details=details, creativity="Média"))
            if UNSAFE.search(output):
                raise ProviderError("Pergunta inadequada para o laboratório.", "invalid_output")
            return self._response(self.external.get_provider_name(), output, "online")
        except ProviderError as exc:
            return self._response(self.local.get_provider_name(), self.local.generate(local_input), "offline", exc.code)
