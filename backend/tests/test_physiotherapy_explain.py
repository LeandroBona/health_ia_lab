import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.ml.physiotherapy import explain, model_manager
from app.ml.physiotherapy.feature_config import CLASSES, FEATURES
from app.ml.physiotherapy.preprocessing import build_preprocessor
from app.schemas.physiotherapy import PatientFeatures

ROOT = "/api/fisioterapia"


def test_patient_explanation_and_shap_additivity(ml_client):
    response = ml_client.get(ROOT + "/patients/PAC-0042/explanation")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["patient_id"] == "PAC-0042"
    assert set(data["probabilities"]) == set(CLASSES)
    assert sum(data["probabilities"].values()) == pytest.approx(1)
    assert len(data["factors"]) == len(FEATURES)
    assert {item["feature"] for item in data["factors"]} == set(FEATURES)
    assert all(item["intensity"] in {"Muito baixo", "Baixo", "Moderado", "Alto", "Muito alto"} for item in data["factors"])
    assert all(item["impact"] > 0 for item in data["positive_factors"])
    assert all(item["impact"] < 0 for item in data["negative_factors"])
    assert data["impact_unit"] == "probability_points"
    record = ml_client.get(ROOT + "/patients/PAC-0042").json()
    frame = pd.DataFrame([{key: record[key] for key in FEATURES}])
    with ml_client.test_sessions() as db:
        raw = explain._values(model_manager.snapshot(), db, frame)
        baseline = np.asarray(explain._explainer(model_manager.snapshot(), db).expected_value)
    predicted = model_manager.snapshot()["pipeline"].predict_proba(frame)[0]
    assert np.allclose(raw.sum(axis=1)[0] + baseline, predicted, atol=1e-6)
    class_index = list(model_manager.snapshot()["pipeline"].classes_).index(data["prediction"])
    assert sum(item["impact"] for item in data["factors"]) == pytest.approx(raw[0, :, class_index].sum())


def test_global_importance_manual_explanation_and_cache_retrain(ml_client):
    first = ml_client.get(ROOT + "/model/feature-importance")
    assert first.status_code == 200, first.text
    data = first.json()
    assert data["sample_source"] == "test" and data["sample_size"] == 60
    assert len(data["features"]) == len(FEATURES)
    assert sum(item["importance"] for item in data["features"]) == pytest.approx(1)
    assert [item["importance"] for item in data["features"]] == sorted((item["importance"] for item in data["features"]), reverse=True)
    record = ml_client.get(ROOT + "/patients/PAC-0042").json()
    features = {key: record[key] for key in FEATURES}
    manual = ml_client.post(ROOT + "/predict/explain", json=features)
    assert manual.status_code == 200, manual.text
    assert manual.json()["probabilities"] == ml_client.post(ROOT + "/predict", json=features).json()["probabilities"]
    assert "patient_id" not in manual.json()
    train = ml_client.post(ROOT + "/model/train")
    assert train.status_code == 200, train.text
    second = ml_client.get(ROOT + "/model/feature-importance")
    assert second.status_code == 200, second.text
    assert second.json()["model_version"] == train.json()["version"] != data["model_version"]
    assert ml_client.get(ROOT + "/patients/PAC-0042/explanation").status_code == 200


def test_simulations_never_change_patient_and_restore(ml_client):
    before = ml_client.get(ROOT + "/patients/PAC-0042").json()
    original_prediction = ml_client.post(ROOT + "/predict/PAC-0042").json()
    for adherence in [0, 30, 60, 100]:
        response = ml_client.post(ROOT + "/simulate", json={"patient_id": "PAC-0042", "changes": {"adesao_exercicios": adherence}})
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["original"]["probabilities"] == original_prediction["probabilities"]
        assert sum(result["simulated"]["probabilities"].values()) == pytest.approx(1)
        assert sum(result["probability_deltas"].values()) == pytest.approx(0)
        assert result["class_changed"] == (result["original"]["prediction"] != result["simulated"]["prediction"])
        assert ml_client.get(ROOT + "/patients/PAC-0042").json() == before
    restored = ml_client.post(ROOT + "/simulate", json={"patient_id": "PAC-0042", "changes": {}}).json()
    assert restored["original"] == restored["simulated"]
    assert ml_client.get(ROOT + "/patients/PAC-0042").json() == before


@pytest.mark.parametrize("changes", [
    {"dor_atual": 40}, {"adesao_exercicios": 150}, {"faltas": -1},
    {"sessoes_realizadas": 31}, {"idade": 30}, {"sexo": 1},
    {"dor_atual": 1.5}, {"faltas": True},
])
def test_simulation_rejects_invalid_changes(ml_client, changes):
    response = ml_client.post(ROOT + "/simulate", json={"patient_id": "PAC-0042", "changes": changes})
    assert response.status_code == 422, response.text


def test_feature_sweep_validation_and_probabilities(ml_client):
    record = ml_client.get(ROOT + "/patients/PAC-0042").json()
    body = {"patient_id": "PAC-0042", "feature": "adesao_exercicios", "values": [0, 25, 50, 75, 100]}
    response = ml_client.post(ROOT + "/simulate/feature", json=body)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["original_value"] == record["adesao_exercicios"]
    assert [item["value"] for item in data["points"]] == body["values"]
    assert all(sum(item["probabilities"].values()) == pytest.approx(1) for item in data["points"])
    assert ml_client.get(ROOT + "/patients/PAC-0042").json() == record
    assert ml_client.post(ROOT + "/simulate/feature", json={**body, "feature": "sexo"}).status_code == 422
    assert ml_client.post(ROOT + "/simulate/feature", json={**body, "values": [0, 101]}).status_code == 422
    assert ml_client.post(ROOT + "/simulate/feature", json={"patient_id": "PAC-0042", "feature": "faltas", "values": [0, 31]}).status_code == 422


def test_logistic_pipeline_has_shap_explanation(ml_client, monkeypatch):
    with ml_client.test_sessions() as db:
        frame = model_manager.training_frame(db, "default")
        pipeline = Pipeline([
            ("preprocessing", build_preprocessor(scale_numeric=True)),
            ("classifier", LogisticRegression(max_iter=2000, random_state=42, class_weight="balanced")),
        ])
        pipeline.fit(frame[FEATURES], frame.resultado)
        bundle = {
            "pipeline": pipeline,
            "metadata": {"algorithm": "LogisticRegression", "version": "comparison"},
            "explanation_background": frame[FEATURES].head(40).to_dict(orient="records"),
            "explanation_test_sample": frame[FEATURES].tail(12).to_dict(orient="records"),
        }
        monkeypatch.setattr(model_manager, "_bundle", bundle)
        features = PatientFeatures.model_validate(frame[FEATURES].iloc[42].to_dict())
        explanation = explain.explain_prediction(features, db)
        assert explanation["impact_unit"] == "logit_units"
        assert len(explanation["factors"]) == len(FEATURES)
        transformed = pipeline.named_steps["preprocessing"].transform(frame[FEATURES].iloc[[42]])
        shap_values = explain._values(bundle, db, frame[FEATURES].iloc[[42]])
        baseline = np.asarray(explain._explainer(bundle, db).expected_value)
        assert np.allclose(shap_values.sum(axis=1)[0] + baseline, pipeline.named_steps["classifier"].decision_function(transformed)[0], atol=1e-5)
