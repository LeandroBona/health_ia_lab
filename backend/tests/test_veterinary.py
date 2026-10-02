import io

import pandas as pd
from sqlalchemy import select

from app.data_generators.veterinary import ANIMAL_COLUMNS, CLASSES, generate_animals
from app.data_generators.veterinary_followup import FOLLOWUP_COLUMNS, generate_followups
from app.ml.veterinary.classification.feature_config import FEATURES
from app.ml.veterinary.anomaly.preprocessing import FEATURES as ANOMALY_FEATURES
from app.ml.veterinary.classification import model_manager as classification_model
from app.ml.veterinary.anomaly import model_manager as anomaly_model
from app.models.veterinary import VeterinaryAnimal, VeterinaryFollowUp


def test_generation_seed_ids_ranges_and_relationships():
    first = generate_animals(120, 7)
    pd.testing.assert_frame_equal(first, generate_animals(120, 7))
    assert first.animal_id.is_unique
    assert first.animal_id.iloc[0] == "VET-0001"
    assert set(first.evolucao) == set(CLASSES)
    for column in ["atividade_percentual", "alimentacao_percentual", "hidratacao_percentual", "medicacao_administrada_percentual", "indice_recuperacao"]:
        assert first[column].between(0, 100).all()
    assert (first.retornos_realizados <= first.retornos_previstos).all()
    followups = generate_followups(first, 7)
    assert followups.followup_id.is_unique
    assert followups.groupby("animal_id").size().between(10, 20).all()
    assert set(followups.animal_id).issubset(set(first.animal_id))
    assert all(count <= first.set_index("animal_id").loc[animal_id, "dias_pos_procedimento"] for animal_id, count in followups.groupby("animal_id").size().items())
    assert set(FEATURES) == set(ANIMAL_COLUMNS) - {"animal_id", "evolucao"}
    assert not set(ANOMALY_FEATURES) & {"animal_id", "followup_id", "timestamp"}


def test_models_endpoints_and_probabilities(veterinary_client):
    client = veterinary_client
    info = client.get("/api/veterinaria/model").json()
    assert info["algorithm"] in {"RandomForestClassifier", "LogisticRegression"}
    assert set(info["metrics"]) == {"accuracy", "precision_macro", "recall_macro", "f1_macro"}
    assert client.get("/api/veterinaria/model/evaluation").status_code == 200
    result = client.post("/api/veterinaria/predict/VET-0001").json()
    assert result["animal_id"] == "VET-0001"
    assert set(result["probabilities"]) == set(CLASSES)
    assert abs(sum(result["probabilities"].values()) - 1) < .00001
    assert isinstance(result["correct"], bool)
    animal = client.get("/api/veterinaria/animals/VET-0001").json()
    manual = client.post("/api/veterinaria/predict", json={key: animal[key] for key in FEATURES}).json()
    assert manual["prediction"] == result["prediction"]
    assert client.post("/api/veterinaria/predict", json={key: animal[key] for key in FEATURES} | {"animal_id": "VET-0001"}).status_code == 422
    assert client.post("/api/veterinaria/predict", json={key: animal[key] for key in FEATURES} | {"evolucao": "evolucao_esperada"}).status_code == 422
    assert classification_model.MODEL_DIR.joinpath("veterinary_model.joblib").is_file()
    assert classification_model.MODEL_DIR.joinpath("model_metadata.json").is_file()
    assert anomaly_model.MODEL_DIR.joinpath("veterinary_anomaly_model.joblib").is_file()
    assert client.post("/api/veterinaria/model/train").json()["version"] == "2.0"
    assert client.post("/api/veterinaria/anomalies/model/train").json()["algorithm"] == "IsolationForest"
    classification_model._bundle = None
    with client.test_sessions() as db:
        classification_model.initialize_model(db)
    assert classification_model.snapshot()["metadata"]["algorithm"] == info["algorithm"]


def test_anomalies_database_and_filters(veterinary_client):
    client = veterinary_client
    response = client.post("/api/veterinaria/anomalies/analyze")
    assert response.status_code == 200
    assert response.json()["anomalies"] > 0
    records = client.get("/api/veterinaria/animals/VET-0001/anomalies").json()
    assert records["animal_id"] == "VET-0001"
    followups = client.get("/api/veterinaria/animals/VET-0001").json()["followups"]
    assert records["items"] == followups
    if followups:
        input_ = {key: followups[0][key] for key in ANOMALY_FEATURES}
        prediction = client.post("/api/veterinaria/anomalies/predict", json=input_).json()
        assert prediction["classification"] in {"padrao", "anomalia"}
        assert isinstance(prediction["anomaly_score"], float)
    filtered = client.get("/api/veterinaria/animals?especie=Gato&page_size=5").json()
    assert all(item["especie"] == "Gato" for item in filtered["items"])
    with client.test_sessions() as db:
        record = db.scalars(select(VeterinaryFollowUp)).first()
        assert record.animal is not None
        assert len(db.get(VeterinaryAnimal, record.animal_id).followups) > 0


def test_exports_and_imports(veterinary_client):
    client = veterinary_client
    for kind in ("animals", "followups"):
        for format_ in ("csv", "xlsx"):
            assert client.get(f"/api/veterinaria/{kind}/dataset/download/{format_}").status_code == 200
    original = generate_animals(3, 91).iloc[[0]].copy()
    original.loc[:, "animal_id"] = "VET-9001"
    buffer = io.BytesIO()
    original.to_csv(buffer, index=False)
    preview = client.post("/api/veterinaria/animals/upload/preview", files={"file": ("animals.csv", buffer.getvalue(), "text/csv")})
    assert preview.status_code == 200, preview.text
    assert preview.json()["importable"] == 1
    token = preview.json()["token"]
    imported = client.post("/api/veterinaria/animals/upload/confirm", json={"token": token})
    assert imported.json()["imported"] == 1
    assert client.post("/api/veterinaria/animals/upload/confirm", json={"token": token}).status_code == 409
    followup = generate_followups(original, 91, fraction=1).iloc[[0]].copy()
    followup.loc[:, "followup_id"] = "FUP-900001"
    buffer = io.BytesIO()
    followup.to_excel(buffer, index=False)
    preview = client.post("/api/veterinaria/followups/upload/preview", files={"file": ("followups.xlsx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert preview.status_code == 200, preview.text
    imported = client.post("/api/veterinaria/followups/upload/confirm", json={"token": preview.json()["token"]})
    assert imported.json()["imported"] == 1
    assert client.get("/api/veterinaria/animals/VET-9001").json()["followups"][0]["followup_id"] == "FUP-900001"
