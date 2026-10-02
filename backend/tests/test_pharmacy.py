import io

import pandas as pd
import pytest

from app.data_generators.pharmacy_adherence import export_adherence, generate_adherence
from app.data_generators.pharmacy_demand import export_demand, generate_demand
from app.ml.pharmacy.adherence import model_manager as adherence_model
from app.ml.pharmacy.adherence.feature_config import FEATURES as ADHERENCE_FEATURES
from app.ml.pharmacy.demand import model_manager as demand_model
from app.ml.pharmacy.demand.features import add_temporal_features, next_period_features
from app.ml.pharmacy.demand.train import chronological_split
from app.schemas.pharmacy import ADHERENCE_COLUMNS, DEMAND_COLUMNS, AdherenceRow, DemandRow
from app.services import pharmacy_dataset


def test_adherence_generation_seed_ranges_and_no_leakage(tmp_path):
    frame = generate_adherence()
    pd.testing.assert_frame_equal(frame, generate_adherence(seed=42))
    assert not frame.equals(generate_adherence(seed=43))
    assert len(frame) == 1000 and frame.patient_id.nunique() == 1000
    assert list(frame.columns) == ADHERENCE_COLUMNS
    assert set(frame.categoria_adesao) == {"alta", "moderada", "baixa"}
    assert not {"patient_id", "adesao_percentual", "categoria_adesao"} & set(ADHERENCE_FEATURES)
    for row in frame.to_dict("records"):
        AdherenceRow.model_validate(row)
    csv, xlsx = export_adherence(frame, tmp_path)
    assert csv.is_file() and xlsx.is_file()
    assert len(pd.read_csv(csv)) == len(pd.read_excel(xlsx)) == 1000


def test_demand_generation_and_temporal_features(tmp_path):
    frame = generate_demand()
    pd.testing.assert_frame_equal(frame, generate_demand(seed=42))
    assert not frame.equals(generate_demand(seed=43))
    assert len(frame) == 720 and list(frame.columns) == DEMAND_COLUMNS
    assert frame.groupby("medication_id").size().eq(36).all()
    for row in frame.to_dict("records"):
        DemandRow.model_validate(row)
    csv, xlsx = export_demand(frame, tmp_path)
    assert csv.is_file() and xlsx.is_file()
    featured = add_temporal_features(frame)
    one = featured[(featured.medication_id == "MED-001") & (featured.period == "2023-07")].iloc[0]
    history = frame[(frame.medication_id == "MED-001") & (frame.period < "2023-07")].sort_values("period")
    assert one.lag_1 == history.iloc[-1].demand
    assert one.rolling_mean_6 == pytest.approx(history.demand.mean())
    future_changed = frame.copy()
    future_changed.loc[(future_changed.medication_id == "MED-001") & (future_changed.period >= "2023-08"), "demand"] = 99999
    before = featured[(featured.medication_id == "MED-001") & (featured.period <= "2023-07")].reset_index(drop=True)
    after = add_temporal_features(future_changed)
    after = after[(after.medication_id == "MED-001") & (after.period <= "2023-07")].reset_index(drop=True)
    pd.testing.assert_frame_equal(before, after)
    train, test, cutoff = chronological_split(featured)
    assert train.period.max() < cutoff == test.period.min()
    features, period = next_period_features(frame[frame.medication_id == "MED-001"])
    assert period == "2026-01" and features["lag_1"] == frame[frame.medication_id == "MED-001"].iloc[-1].demand


def test_pharmacy_models_and_endpoints(pharmacy_client):
    client = pharmacy_client
    stats = client.get("/api/farmacia/adesao/stats").json()
    assert stats["total_records"] == 1000
    assert client.get("/api/farmacia/demanda/stats").json()["records"] == 720
    model = client.get("/api/farmacia/adesao/model").json()
    assert model["algorithm"] in {"LogisticRegression", "RandomForestClassifier"}
    assert model["training_samples"] == 800 and model["test_samples"] == 200
    assert hasattr(adherence_model.snapshot()["pipeline"], "predict_proba")
    result = client.post("/api/farmacia/adesao/predict/FAR-0001").json()
    assert result["patient_id"] == "FAR-0001"
    assert sum(result["probabilities"].values()) == pytest.approx(1, abs=1e-5)
    manual = client.get("/api/farmacia/adesao/patients/FAR-0001").json()
    features = {key: manual[key] for key in ADHERENCE_FEATURES}
    assert client.post("/api/farmacia/adesao/predict", json=features).status_code == 200
    assert client.post("/api/farmacia/adesao/predict", json={**features, "idade": -1}).status_code == 422
    assert client.get("/api/farmacia/adesao/model/evaluation").json()["selected_model"] == model["algorithm"]
    paged = client.get("/api/farmacia/adesao/patients?page=2&page_size=10&search=FAR-00&categoria=alta").json()
    assert len(paged["items"]) == 10 and all(item["categoria_adesao"] == "alta" for item in paged["items"])
    assert client.get("/api/farmacia/adesao/patients/MISSING").status_code == 404
    demand = client.get("/api/farmacia/demanda/model").json()
    assert demand["algorithm"] in {"LinearRegression", "RandomForestRegressor"}
    assert demand["train_last_period"] < demand["test_first_period"]
    assert demand["metrics"]["mae"] >= 0
    assert demand_model.snapshot()["pipeline"] is not None
    forecast = client.post("/api/farmacia/demanda/predict/MED-001").json()
    assert forecast["period"] == "2026-01" and forecast["prediction"] >= 0
    detail = client.get("/api/farmacia/demanda/medications/MED-001").json()
    assert len(detail["history"]) == 36 and detail["test_predictions"]
    assert client.get("/api/farmacia/demanda/medications?page=1&page_size=5").json()["total"] == 20
    assert client.get("/api/farmacia/demanda/model/evaluation").json()["test_predictions"]
    assert client.get("/api/farmacia/demanda/medications/MISSING").status_code == 404


@pytest.mark.parametrize("kind", ["adesao", "demanda"])
@pytest.mark.parametrize("extension", ["csv", "xlsx"])
def test_pharmacy_upload_preview_confirm_duplicate(pharmacy_client, kind, extension):
    client = pharmacy_client
    original = generate_adherence(1) if kind == "adesao" else generate_demand(1, 12).iloc[:1]
    if kind == "adesao":
        original.loc[:, "patient_id"] = "FAR-9001"
    else:
        original.loc[:, "medication_id"] = "MED-901"
    buffer = io.BytesIO()
    if extension == "csv":
        original.to_csv(buffer, index=False)
    else:
        original.to_excel(buffer, index=False)
    content = buffer.getvalue()
    path = f"/api/farmacia/{kind}/upload/preview"
    response = client.post(path, files={"file": (f"data.{extension}", content)})
    assert response.status_code == 200, response.text
    preview = response.json()
    assert preview["record_count"] == 1 and preview["missing_total"] == 0
    result = client.post(f"/api/farmacia/{kind}/upload/confirm", json={"token": preview["token"]})
    assert result.json()["imported"] == 1
    assert client.post(f"/api/farmacia/{kind}/upload/confirm", json={"token": preview["token"]}).status_code == 409
    again = client.post(path, files={"file": (f"data.{extension}", content)}).json()
    assert again["duplicates"] == 1
    assert client.post(f"/api/farmacia/{kind}/upload/confirm", json={"token": again["token"]}).json()["ignored"] == 1


def test_upload_rejects_invalid_and_missing_columns(client):
    assert client.post("/api/farmacia/adesao/upload/preview", files={"file": ("bad.txt", b"hello")}).status_code == 415
    frame = generate_adherence(1).drop(columns=["recebe_lembretes"])
    buffer = io.BytesIO()
    frame.to_csv(buffer, index=False)
    response = client.post("/api/farmacia/adesao/upload/preview", files={"file": ("bad.csv", buffer.getvalue())})
    assert response.status_code == 422
    assert response.json()["missing_columns"] == ["recebe_lembretes"]


def test_pharmacy_persistence_reload(pharmacy_client, monkeypatch):
    with pharmacy_client.test_sessions() as db:
        original_adherence = adherence_model.snapshot()["metadata"]["algorithm"]
        original_demand = demand_model.snapshot()["metadata"]["algorithm"]
        monkeypatch.setattr(adherence_model, "_bundle", None)
        monkeypatch.setattr(demand_model, "_bundle", None)
        adherence_model.initialize_model(db)
        demand_model.initialize_model(db)
        assert adherence_model.snapshot()["metadata"]["algorithm"] == original_adherence
        assert demand_model.snapshot()["metadata"]["algorithm"] == original_demand
        assert adherence_model.train_model(db)["version"] == "2.0"
        assert demand_model.train_model(db)["version"] == "2.0"
        assert pharmacy_dataset.default_file("adesao", "csv").is_file()
