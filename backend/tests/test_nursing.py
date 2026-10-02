import io

import pandas as pd
import pytest
from sqlalchemy import func, select

from app.data_generators.nursing import generate_measurements
from app.ml.nursing import anomaly_service
from app.models.nursing import NursingMeasurement
from app.schemas.nursing import FEATURES, REQUIRED_COLUMNS
from app.services.nursing_dataset import validate_frame
from app.services.physiotherapy_validation import DatasetError


def test_generator_reproducible_and_coherent():
    first = generate_measurements(500, 42)
    second = generate_measurements(500, 42)
    pd.testing.assert_frame_equal(first, second)
    assert first.patient_id.nunique() == 500
    assert first.measurement_id.is_unique
    assert 5000 <= len(first) <= 15000
    assert 0.05 <= (first.estado == "alterado").mean() <= 0.1
    assert list(first.columns) == REQUIRED_COLUMNS
    assert (first.pressao_sistolica > first.pressao_diastolica).all()
    assert validate_frame(first, "monitoramento.csv")[0]["record_count"] == len(first)
    changed = generate_measurements(20, 7)
    assert not changed.equals(first.head(len(changed)))


def test_missing_column_rejected():
    frame = generate_measurements(1)
    with pytest.raises(DatasetError) as error:
        validate_frame(frame.drop(columns=["saturacao"]), "invalid.csv")
    assert error.value.body["missing_columns"] == ["saturacao"]


def test_nursing_endpoints_and_model(nursing_client):
    client = nursing_client
    stats = client.get("/api/enfermagem/stats").json()
    assert stats["total_patients"] == 500
    assert 5000 <= stats["total_measurements"] <= 15000
    assert stats["anomalies"] > 0
    assert client.get("/api/enfermagem/model").json()["algorithm"] == "IsolationForest"
    assert client.get("/api/enfermagem/model/evaluation").json()["confusion_matrix"]
    patients = client.get("/api/enfermagem/patients", params={"page": 2, "page_size": 10}).json()
    assert len(patients["items"]) == 10
    assert patients["items"][0]["patient_id"] == "ENF-0011"
    found = client.get("/api/enfermagem/patients", params={"search": "ENF-0012"}).json()
    assert found["total"] == 1
    detail = client.get("/api/enfermagem/patients/ENF-0012").json()
    assert detail["measurements"] >= 10
    timeline = client.get("/api/enfermagem/patients/ENF-0012/measurements").json()
    assert timeline["total"] == detail["measurements"]
    measurement = client.get("/api/enfermagem/measurements/MED-000001").json()
    assert "patient_average" in measurement["comparisons"]["temperatura"]
    anomalies = client.get("/api/enfermagem/measurements", params={"classification": "anomalia"}).json()
    assert anomalies["items"][0]["classification"] == "anomalia"
    assert anomalies["total"] == stats["anomalies"]
    assert client.get("/api/enfermagem/dataset/explore?column=temperatura").json()["type"] == "numeric"
    timeline = client.get("/api/enfermagem/dataset/timeline").json()
    assert sum(day["measurements"] for day in timeline) == stats["total_measurements"]


def test_manual_prediction_is_read_only_and_state_not_feature(nursing_client):
    client = nursing_client
    assert "estado" not in FEATURES
    patient = client.get("/api/enfermagem/patients/ENF-0012").json()
    with client.test_sessions() as db:
        before = db.scalar(select(func.count()).select_from(NursingMeasurement))
    response = client.post("/api/enfermagem/anomalies/predict", json=patient["averages"])
    assert response.status_code == 200
    assert response.json()["classification"] in {"padrao", "anomalia"}
    assert client.post("/api/enfermagem/anomalies/predict", json={**patient["averages"], "saturacao": 150}).status_code == 422
    with client.test_sessions() as db:
        assert db.scalar(select(func.count()).select_from(NursingMeasurement)) == before
    assert client.get("/api/dashboard").json()["models"] >= 1


@pytest.mark.parametrize("format", ["csv", "xlsx"])
def test_upload_preview_confirm_and_duplicate(nursing_client, format):
    client = nursing_client
    frame = generate_measurements(1).head(2).copy()
    frame["patient_id"] = "ENF-9999"
    frame["measurement_id"] = ["MED-999998", "MED-999999"]
    buffer = io.BytesIO()
    if format == "csv":
        buffer.write(frame.to_csv(index=False).encode())
    else:
        frame.to_excel(buffer, index=False)
    payload = buffer.getvalue()
    preview = client.post("/api/enfermagem/upload/preview", files={"file": (f"upload.{format}", payload)}).json()
    assert preview["success"] is True
    assert preview["record_count"] == 2
    assert preview["importable"] == 2
    result = client.post("/api/enfermagem/upload/confirm", json={"token": preview["token"]}).json()
    assert result["imported"] == 2
    assert client.get("/api/enfermagem/patients/ENF-9999").status_code == 200
    assert client.post("/api/enfermagem/upload/confirm", json={"token": preview["token"]}).status_code == 409
    repeat = client.post("/api/enfermagem/upload/preview", files={"file": (f"upload.{format}", payload)}).json()
    assert repeat["duplicates"] == 2
    ignored = client.post("/api/enfermagem/upload/confirm", json={"token": repeat["token"]}).json()
    assert ignored["ignored"] == 2


def test_invalid_uploads(nursing_client):
    client = nursing_client
    assert client.post("/api/enfermagem/upload/preview", files={"file": ("bad.txt", b"x")}).status_code == 415
    frame = generate_measurements(1).head(1).drop(columns=["saturacao"])
    response = client.post("/api/enfermagem/upload/preview", files={"file": ("bad.csv", frame.to_csv(index=False).encode())})
    assert response.status_code == 422
    assert response.json()["missing_columns"] == ["saturacao"]


def test_retraining_keeps_analysis_compatible(nursing_client):
    client = nursing_client
    old = client.get("/api/enfermagem/model").json()["version"]
    new = client.post("/api/enfermagem/model/train").json()["version"]
    assert new != old
    assert client.post("/api/enfermagem/anomalies/analyze").json()["anomalies"] > 0
    with client.test_sessions() as db:
        anomaly_service.initialize_model(db)
    assert client.get("/api/enfermagem/model").json()["version"] == new
