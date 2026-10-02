import json
import math
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Module = Literal["fisioterapia", "enfermagem", "farmacia", "veterinaria", "psicologia"]
AnalysisType = Literal["prediction", "anomaly", "demand", "nlp"]
Level = Literal["Simples", "Acadêmica", "Técnica"]

ALLOWED_TYPES = {
    "fisioterapia": {"prediction"},
    "enfermagem": {"anomaly"},
    "farmacia": {"prediction", "demand"},
    "veterinaria": {"prediction", "anomaly"},
    "psicologia": {"nlp"},
}
ALLOWED_FIELDS = {
    "prediction": {"prediction", "probabilities", "algorithm", "features", "factors"},
    "anomaly": {"classification", "score", "anomaly_index", "algorithm", "features", "comparison"},
    "demand": {"prediction", "period", "algorithm", "mae", "trend", "history_summary", "features"},
    "nlp": {"theme", "probabilities", "keywords", "similarity", "cluster", "algorithm"},
}


class ExplainRequest(BaseModel):
    module: Module
    analysis_type: AnalysisType
    data: dict[str, Any]
    level: Level = "Simples"
    provider: Literal["auto", "local"] = "auto"
    source_history_id: str | None = Field(default=None, max_length=36)
    record_reference: str | None = Field(default=None, max_length=60, pattern=r"^[A-Za-z0-9_-]+$")

    @model_validator(mode="after")
    def validate_payload(self):
        if self.analysis_type not in ALLOWED_TYPES[self.module]:
            raise ValueError("Tipo de análise incompatível com o módulo.")
        if not self.data:
            raise ValueError("Informe o resultado estruturado do modelo.")
        if len(json.dumps(self.data, ensure_ascii=False, allow_nan=False)) > 6000:
            raise ValueError("Resultado muito extenso. Envie apenas os dados necessários.")
        if not set(self.data).issubset(ALLOWED_FIELDS[self.analysis_type]):
            raise ValueError("O resultado contém campos não permitidos para a explicação.")
        return self


class ContentRequest(BaseModel):
    topic: Literal["Machine Learning", "Random Forest", "Regressão", "Detecção de anomalias", "Isolation Forest", "NLP", "TF-IDF", "Clustering", "Visão Computacional", "Landmarks", "IA Generativa"]
    level: Literal["Básico", "Intermediário", "Avançado"] = "Básico"
    length: Literal["Curto", "Médio", "Longo"] = "Curto"
    creativity: Literal["Baixa", "Média", "Alta"] = "Média"


class QuestionRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=80)
    result: str = Field(default="", max_length=250)


class PromptFields(BaseModel):
    context: str = Field(default="", max_length=500)
    role: str = Field(default="", max_length=300)
    objective: str = Field(default="", max_length=500)
    data: str = Field(default="", max_length=1000)
    constraints: str = Field(default="", max_length=500)
    output_format: str = Field(default="", max_length=300)
    creativity: Literal["Baixa", "Média", "Alta"] = "Baixa"

    @field_validator("context", "role", "objective", "data", "constraints", "output_format")
    @classmethod
    def clean(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def require_objective(self):
        if not self.objective:
            raise ValueError("Informe o objetivo do prompt.")
        return self


def clean_value(value: Any, depth: int = 0) -> Any:
    """Bound arbitrary client data to a small, non-identifying structured summary."""
    if depth > 2:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise ValueError("Valores numéricos devem ser finitos.")
        return value
    if isinstance(value, str):
        return value[:100].strip()
    if isinstance(value, list):
        return [clean_value(item, depth + 1) for item in value[:5]]
    if isinstance(value, dict):
        return {str(key)[:60]: clean_value(item, depth + 1) for key, item in list(value.items())[:12] if not any(token in str(key).lower() for token in ("id", "nome", "cpf", "email", "telefone", "texto"))}
    return None


def minimize(request: ExplainRequest) -> dict[str, Any]:
    return {key: clean_value(value) for key, value in request.data.items() if key in ALLOWED_FIELDS[request.analysis_type]}
