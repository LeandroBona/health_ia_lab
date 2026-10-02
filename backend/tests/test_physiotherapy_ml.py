import json

import pytest
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

from app.ml.physiotherapy import model_manager
from app.ml.physiotherapy.feature_config import CLASSES, FEATURES
from app.models.physiotherapy import PhysiotherapyPatient

PREFIX = "/api/fisioterapia"


def test_training_evaluation_and_pipeline(ml_client):
    info = ml_client.get(PREFIX + "/model").json()
    assert info["status"] == "ready"
    assert info["training_samples"] == 800 and info["test_samples"] == 200
    assert info["version"] == "1.0" and info["dataset_source"] == "default"
    assert "patient_id" not in info["features"] and "resultado" not in info["features"]
    assert set(info["features"]) == set(FEATURES) and len(FEATURES) == 16
    assert set(info["algorithms"]) == {"RandomForestClassifier", "LogisticRegression"}
    assert info["metrics"]["f1_macro"] == max(value["f1_macro"] for value in info["algorithms"].values())
    bundle = model_manager.snapshot()
    assert isinstance(bundle["pipeline"], Pipeline)
    assert bundle["pipeline"].named_steps["preprocessing"].remainder == "drop"
    with ml_client.test_sessions() as db:
        frame = model_manager.training_frame(db, "default")
    test_ids = [key for key, value in bundle["membership"].items() if value["partition"] == "test"]
    test = frame[frame.patient_id.isin(test_ids)]
    predicted = bundle["pipeline"].predict(test[FEATURES])
    evaluation = ml_client.get(PREFIX + "/model/evaluation").json()
    assert evaluation["f1_macro"] == pytest.approx(f1_score(test.resultado, predicted, labels=CLASSES, average="macro"))
    assert evaluation["confusion_matrix"] == confusion_matrix(test.resultado, predicted, labels=CLASSES).tolist()
    assert sum(sum(row) for row in evaluation["confusion_matrix"]) == 200
    assert sum(metrics["support"] for metrics in evaluation["per_class"].values()) == 200
    assert ml_client.get("/api/dashboard").json()["models"] == 1


def test_predictions_no_target_leakage_and_partition(ml_client):
    record = ml_client.get(PREFIX + "/patients/PAC-0001").json()
    features = {key: record[key] for key in FEATURES}
    manual = ml_client.post(PREFIX + "/predict", json=features).json()
    existing = ml_client.post(PREFIX + "/predict/PAC-0001").json()
    assert manual["probabilities"] == existing["probabilities"]
    assert sum(existing["probabilities"].values()) == pytest.approx(1)
    assert existing["confidence"] == max(existing["probabilities"].values())
    assert existing["correct"] == (existing["prediction"] == record["resultado"])
    assert existing["partition"] in {"train", "test"}
    with ml_client.test_sessions() as db:
        patient = db.get(PhysiotherapyPatient, "PAC-0001")
        patient.resultado = next(label for label in CLASSES if label != patient.resultado)
        db.commit()
    changed = ml_client.post(PREFIX + "/predict/PAC-0001").json()
    assert changed["prediction"] == existing["prediction"]
    assert changed["probabilities"] == existing["probabilities"]
    assert changed["partition"] == "unseen_or_changed"
    assert ml_client.get(PREFIX + "/model").json()["dataset_changed"] is True
    assert ml_client.post(PREFIX + "/predict/PAC-9999").status_code == 404


def test_persistence_no_automatic_retraining_and_version(ml_client, monkeypatch):
    artifact = model_manager.MODEL_DIR / "physiotherapy_model.joblib"
    metadata_file = model_manager.MODEL_DIR / "model_metadata.json"
    assert artifact.exists() and metadata_file.exists()
    version = json.loads(metadata_file.read_text())["version"]
    modified = artifact.stat().st_mtime_ns
    response = ml_client.post(PREFIX + "/model/train")
    assert response.status_code == 200, response.text
    assert response.json()["version"] != version
    assert response.json()["dataset_source"] == "database"
    modified = artifact.stat().st_mtime_ns
    old_prediction = ml_client.post(PREFIX + "/predict/PAC-0001").json()
    monkeypatch.setattr(model_manager, "_bundle", None)
    def unexpected_train(*args, **kwargs):
        pytest.fail("An existing valid artifact must not be retrained")
    monkeypatch.setattr(model_manager, "train_model", unexpected_train)
    with ml_client.test_sessions() as db:
        model_manager.initialize_model(db)
    assert artifact.stat().st_mtime_ns == modified
    assert ml_client.post(PREFIX + "/predict/PAC-0001").json() == old_prediction


@pytest.mark.parametrize("key,value", [("dor_atual", 40), ("adesao_exercicios", 150), ("idade", -2), ("sessoes_realizadas", 99), ("sexo", "desconhecido"), ("idade", "abc"), ("idade", 21.5), ("faltas", 30)])
def test_manual_validation(client, key, value):
    record = client.get(PREFIX + "/patients/PAC-0001").json()
    features = {column: record[column] for column in FEATURES}
    features[key] = value
    response = client.post(PREFIX + "/predict", json=features)
    assert response.status_code == 422 and response.json()["success"] is False


def test_missing_fields_and_forbidden_target(client):
    record = client.get(PREFIX + "/patients/PAC-0001").json()
    assert client.post(PREFIX + "/predict", json=record).status_code == 422
    features = {key: record[key] for key in FEATURES if key != "idade"}
    assert client.post(PREFIX + "/predict", json=features).status_code == 422


def test_insufficient_data_preserves_previous_model(ml_client):
    version = ml_client.get(PREFIX + "/model").json()["version"]
    ml_client.post(PREFIX + "/dataset/regenerate", json={"size": 10, "confirm": True})
    response = ml_client.post(PREFIX + "/model/train")
    assert response.status_code == 422 and "30 registros" in response.json()["message"]
    assert ml_client.get(PREFIX + "/model").json()["version"] == version
