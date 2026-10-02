from io import BytesIO

import joblib
import pandas as pd
import pytest
from sqlalchemy import func, select

from app.data_generators.psychology import AGE_RANGES, COLUMNS, CONTEXTS, THEMES, export_reports, generate_reports
from app.ml.psychology import model_manager
from app.ml.psychology.classification import classify_text
from app.ml.psychology.clustering import approximate_group
from app.ml.psychology.keywords import extract_keywords
from app.ml.psychology.preprocessing import content_tokens, make_vectorizer, normalize_text, processing_details
from app.ml.psychology.similarity import find_similar
from app.models.psychology import PsychologyDataset, PsychologyRecord


def test_generation_seed_content_and_export(tmp_path):
    first = generate_reports(1000, 42)
    pd.testing.assert_frame_equal(first, generate_reports(1000, 42))
    assert not first.equals(generate_reports(1000, 43))
    assert first.columns.tolist() == COLUMNS
    assert first.record_id.is_unique
    assert first.record_id.iloc[[0, -1]].tolist() == ["PSI-0001", "PSI-1000"]
    assert set(first.tema_principal) == set(THEMES)
    assert set(first.contexto) <= set(CONTEXTS)
    assert set(first.idade_faixa) <= set(AGE_RANGES)
    assert first.texto.str.len().min() > 10
    assert first.texto.str.count(r"\.").between(1, 5).all()
    assert not first.texto.str.contains(r"(?i)meu tema é|tema principal|paciente apresenta").any()
    export_reports(first, tmp_path)
    assert len(pd.read_csv(tmp_path / "relatos_psicologia.csv")) == 1000
    assert len(pd.read_excel(tmp_path / "relatos_psicologia.xlsx")) == 1000


def test_preprocessing_and_tfidf():
    text = "  Estou dormindo pouco, por causa das provas!  "
    assert normalize_text(text) == "estou dormindo pouco por causa das provas"
    details = processing_details(text)
    assert "estou" in details["stopwords_removed"]
    assert "dormindo" in content_tokens(text)
    assert "provas" in details["terms_kept"]
    vectorizer = make_vectorizer(min_df=1)
    matrix = vectorizer.fit_transform([text, "As provas e os estudos organizaram a semana."])
    assert matrix.shape[0] == 2 and matrix.shape[1] > 0
    assert any("provas" in term for term in vectorizer.get_feature_names_out())


def test_model_pipeline_probabilities_clusters_similarity_and_persistence(psychology_client):
    bundle = model_manager.snapshot()
    pipeline = bundle["pipeline"]
    assert list(pipeline.named_steps) == ["tfidf", "classifier"]
    assert bundle["metadata"]["input"] == ["texto"]
    assert bundle["metadata"]["target"] == "tema_principal"
    assert "tema_principal" not in bundle["vectorizer"].get_feature_names_out()
    assert len(bundle["cluster_summary"]) == 5
    assert sum(group["quantidade"] for group in bundle["cluster_summary"]) == 240
    assert all(group["top_terms"] for group in bundle["cluster_summary"])
    text = bundle["records"][0]["texto"]
    result = classify_text(text, bundle)
    assert result["prediction"] in THEMES
    assert set(result["probabilities"]) == set(THEMES)
    assert sum(result["probabilities"].values()) == pytest.approx(1, abs=1e-5)
    assert extract_keywords(text, bundle["vectorizer"])
    assert approximate_group(text, bundle)["cluster_id"] in range(1, 6)
    assert all(item["record_id"] != bundle["records"][0]["record_id"] for item in find_similar(text, bundle))
    assert all(normalize_text(item["text"]) != normalize_text(text) for item in find_similar(text, bundle))
    loaded = joblib.load(model_manager.MODEL_DIR / "psychology_topic_model.joblib")
    assert loaded["pipeline"].predict([text]).tolist() == pipeline.predict([text]).tolist()
    assert (model_manager.MODEL_DIR / "model_metadata.json").exists()


def test_api_analysis_and_dataset_relationship(psychology_client):
    api = psychology_client
    with api.test_sessions() as db:
        assert db.scalar(select(func.count()).select_from(PsychologyRecord)) == 240
        assert db.scalar(select(func.count()).select_from(PsychologyDataset)) == 1
        assert db.get(PsychologyRecord, "PSI-0001").dataset_id == "default-psychology"
    for path in ["/stats", "/records", "/records/PSI-0001", "/terms?limit=5&tema=Estudos", "/clusters", "/model", "/model/evaluation"]:
        response = api.get("/api/psicologia" + path)
        assert response.status_code == 200, response.text
    assert api.get("/api/psicologia/records/PSI-9999").status_code == 404
    record = api.get("/api/psicologia/records/PSI-0001").json()
    assert record["analysis"]["original_text"] == record["texto"]
    assert isinstance(record["correct"], bool)
    assert api.get("/api/psicologia/records?tema=Estudos").json()["total"] > 0
    assert api.get("/api/psicologia/terms?tema=Inexistente").status_code == 422
    assert api.get("/api/psicologia/dataset/download/csv").status_code == 200
    assert api.get("/api/psicologia/dataset/download/xlsx").status_code == 200
    for endpoint in ["keywords", "classify", "similarity", "analyze"]:
        response = api.post("/api/psicologia/" + endpoint, json={"text": record["texto"]})
        assert response.status_code == 200, response.text
    assert api.post("/api/psicologia/analyze", json={"text": "   "}).status_code == 422
    analysis = api.post("/api/psicologia/analyze", json={"text": record["texto"]}).json()
    assert analysis["processing"]["tokens"]
    assert analysis["tfidf"]
    assert analysis["similar"]
    assert all(item["record_id"] != record["record_id"] for item in analysis["similar"])
    assert api.post("/api/psicologia/model/train").status_code == 200


@pytest.mark.parametrize("format_", ["csv", "xlsx"])
def test_upload_preview_and_confirm(psychology_client, format_):
    frame = generate_reports(12, 29).iloc[:1].copy()
    frame.loc[:, "record_id"] = "PSI-9001"
    stream = BytesIO()
    if format_ == "csv":
        frame.to_csv(stream, index=False)
    else:
        frame.to_excel(stream, index=False)
    response = psychology_client.post("/api/psicologia/upload/preview", files={"file": (f"novos.{format_}", stream.getvalue())})
    assert response.status_code == 200, response.text
    info = response.json()
    assert info["record_count"] == info["importable"] == 1
    assert info["column_count"] == 7
    assert info["average_text_length"] > 10
    assert info["preview"][0]["record_id"] == "PSI-9001"
    confirmed = psychology_client.post("/api/psicologia/upload/confirm", json={"token": info["token"]})
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["imported"] == 1
    assert psychology_client.get("/api/psicologia/records/PSI-9001").status_code == 200
    assert psychology_client.post("/api/psicologia/upload/confirm", json={"token": info["token"]}).status_code == 409
    again = psychology_client.post("/api/psicologia/upload/preview", files={"file": (f"novos.{format_}", stream.getvalue())})
    assert again.json()["duplicates"] == 1


def test_upload_rejects_empty_text(psychology_client):
    frame = generate_reports(12, 42).iloc[:1].copy()
    frame.loc[:, "record_id"] = "PSI-9002"
    frame.loc[:, "texto"] = ""
    response = psychology_client.post("/api/psicologia/upload/preview", files={"file": ("vazio.csv", frame.to_csv(index=False).encode())})
    assert response.status_code == 422
    assert "inválidos" in response.json()["message"]
