import io
from urllib.error import HTTPError, URLError

import pytest

from app.services.llm.base import GenerationInput
from app.services.llm.llm_service import LLMService
from app.services.llm.local_provider import LocalTemplateProvider
from app.services.llm.openai_provider import OpenAIProvider, ProviderError
from app.services.llm.prompt_builder import percent
from app.services.llm.schemas import ExplainRequest
from app.services.analysis_history import record


@pytest.mark.parametrize("module,kind,data,expected", [
    ("fisioterapia", "prediction", {"prediction": "recuperacao_lenta", "probabilities": {"recuperacao_lenta": 0.72}}, "72%"),
    ("enfermagem", "anomaly", {"classification": "anomalia", "anomaly_index": 0.314}, "0.314"),
    ("farmacia", "prediction", {"prediction": "moderada", "probabilities": {"moderada": 0.72}}, "72%"),
    ("farmacia", "demand", {"prediction": 512, "period": "2026-11"}, "512"),
    ("veterinaria", "prediction", {"prediction": "evolucao_esperada", "probabilities": {"evolucao_esperada": 0.72}}, "72%"),
    ("veterinaria", "anomaly", {"classification": "anomalia", "anomaly_index": 0.11}, "0.11"),
    ("psicologia", "nlp", {"theme": "Estudos", "probabilities": {"Estudos": 0.72}, "keywords": [{"term": "provas", "score": 0.5}], "cluster": "Grupo 2"}, "72%"),
])
def test_local_explanations_keep_outputs(module, kind, data, expected):
    response = LLMService(external=OpenAIProvider(api_key="")).explain(ExplainRequest(module=module, analysis_type=kind, data=data))
    assert response["provider"] == "Local Template"
    assert expected in response["explanation"]
    assert response["mode"] == "offline"


def test_percentage_exact():
    assert percent(0.72) == "72%"
    assert percent(0.6805) == "68.05%"
    assert percent(0.8) == "80%"


class FakeExternal(OpenAIProvider):
    def __init__(self, output):
        super().__init__(api_key="test-only", model="fake")
        self.output = output

    def generate(self, request: GenerationInput) -> str:
        if isinstance(self.output, Exception):
            raise self.output
        return self.output


def test_external_selection_and_number_guard():
    request = ExplainRequest(module="fisioterapia", analysis_type="prediction", data={"prediction": "recuperacao_lenta", "probabilities": {"recuperacao_lenta": 0.72}})
    response = LLMService(external=FakeExternal("Esta saída é uma associação estatística em dados sintéticos.")).explain(request)
    assert response["provider"] == "OpenAI"
    assert "72%" in response["explanation"]
    invalid = LLMService(external=FakeExternal("A previsão é 80%." )).explain(request)
    assert invalid["provider"] == "Local Template"
    assert invalid["fallback_reason"] == "invalid_output"
    assert "72%" in invalid["explanation"]
    assert "80%" not in invalid["explanation"]


@pytest.mark.parametrize("code", ["network", "invalid_key", "rate_limit", "server_error"])
def test_external_failure_falls_back(code):
    service = LLMService(external=FakeExternal(ProviderError("Falha", code)))
    response = service.explain(ExplainRequest(module="enfermagem", analysis_type="anomaly", data={"classification": "anomalia", "score": 0.27}))
    assert response["mode"] == "offline"
    assert response["fallback_reason"] == code
    assert "0.27" in response["explanation"]


@pytest.mark.parametrize("status,expected", [(401, "invalid_key"), (429, "rate_limit"), (500, "server_error")])
def test_http_errors_are_sanitized(monkeypatch, status, expected):
    def fail(*args, **kwargs):
        raise HTTPError("https://api.openai.com/v1/responses", status, "secret-data", {}, io.BytesIO(b"secret-data"))
    monkeypatch.setattr("app.services.llm.openai_provider.urlopen", fail)
    with pytest.raises(ProviderError) as caught:
        OpenAIProvider(api_key="test-only").generate(GenerationInput(task="content", details="hello"))
    assert caught.value.code == expected
    assert "secret-data" not in str(caught.value)


def test_network_error_is_sanitized(monkeypatch):
    monkeypatch.setattr("app.services.llm.openai_provider.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(URLError("secret-url")))
    with pytest.raises(ProviderError) as caught:
        OpenAIProvider(api_key="test-only").generate(GenerationInput(task="content", details="hello"))
    assert caught.value.code == "network"
    assert "secret-url" not in str(caught.value)


def test_endpoints_offline_and_validation(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert client.get("/api/generative/status").json()["mode"] == "offline"
    result = client.post("/api/generative/explain", json={"module": "fisioterapia", "analysis_type": "prediction", "data": {"prediction": "recuperacao_lenta", "probabilities": {"recuperacao_lenta": 0.72}}})
    assert result.status_code == 200
    assert "72%" in result.json()["explanation"]
    assert client.post("/api/generative/explain", json={"module": "fisioterapia", "analysis_type": "prediction", "data": {"patient_id": "secret", "prediction": "x"}}).status_code == 422
    assert client.post("/api/generative/content", json={"topic": "TF-IDF"}).status_code == 200
    assert client.post("/api/generative/question", json={"topic": "classificação"}).status_code == 200
    assert client.post("/api/generative/prompt/execute", json={"objective": "Explique um modelo"}).status_code == 503


def test_local_provider_is_deterministic():
    provider = LocalTemplateProvider()
    request = GenerationInput(task="content", topic="TF-IDF", level="Básico")
    assert provider.generate(request) == provider.generate(request)


def test_explanation_links_to_prediction_even_after_simulation(client):
    with client.test_sessions() as db:
        prediction = record(db, module="fisioterapia", analysis_type="physiotherapy_prediction", model_name="RandomForest", record_reference="PAC-0001", result_summary="Categoria sintética.")
        record(db, module="fisioterapia", analysis_type="physiotherapy_simulation", model_name="RandomForest", record_reference="PAC-0001", result_summary="Cenário sintético.")
        prediction_id = prediction.id
    response = client.post("/api/generative/explain", json={"module":"fisioterapia", "analysis_type":"prediction", "record_reference":"PAC-0001", "data":{"prediction":"recuperacao_lenta", "probabilities":{"recuperacao_lenta":0.72}}})
    assert response.status_code == 200, response.text
    detail = client.get(f"/api/history/{response.json()['history_id']}").json()
    assert detail["source_history_id"] == prediction_id
