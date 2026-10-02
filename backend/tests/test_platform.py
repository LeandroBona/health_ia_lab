from app.services.analysis_history import record


def test_catalog_status_and_dataset_details(client):
    models = client.get("/api/models")
    assert models.status_code == 200, models.text
    ids = {item["id"] for item in models.json()["items"]}
    assert {"physiotherapy-classification", "nursing-anomaly", "pharmacy-demand", "psychology-classification", "vision-pose", "generative-explanation"}.issubset(ids)
    datasets = client.get("/api/datasets")
    assert datasets.status_code == 200, datasets.text
    assert len(datasets.json()["items"]) == 7
    for item in datasets.json()["items"]:
        detail = client.get(f"/api/datasets/{item['id']}")
        assert detail.status_code == 200, detail.text
        assert detail.json()["synthetic"] is True
        assert detail.json()["column_count"] > 0
        assert detail.json()["records"] >= 0
    assert client.get("/api/datasets/unknown").status_code == 404
    status = client.get("/api/system/status")
    assert status.status_code == 200
    assert status.json()["database"] == "ok"
    assert status.json()["vision"]["status"] == "browser"


def test_history_filters_details_and_no_raw_payload(client):
    with client.test_sessions() as db:
        source = record(db, module="fisioterapia", analysis_type="physiotherapy_prediction", model_name="Random Forest", model_version="1.0", record_reference="PAC-0001", result_summary="Categoria sintética: recuperação lenta; probabilidade 0.72.")
        explanation = record(db, module="ia-generativa", analysis_type="generative_explanation", model_name="Local Template", record_reference="PAC-0001", source_history_id=source.id, result_summary="Explicação local; conteúdo não armazenado.")
        source_id, explanation_id = source.id, explanation.id
    response = client.get("/api/history", params={"module": "fisioterapia"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["record_reference"] == "PAC-0001"
    detail = client.get(f"/api/history/{explanation_id}").json()
    assert detail["source_history_id"] == source_id
    assert "prompt" not in detail
    assert client.get("/api/history/unknown").status_code == 404
    assert client.get("/api/history", params={"analysis_type": "unknown"}).status_code == 422


def test_existing_prediction_is_recorded_without_changing_result(ml_client):
    before = ml_client.get("/api/history").json()["total"]
    prediction = ml_client.post("/api/fisioterapia/predict/PAC-0001")
    assert prediction.status_code == 200
    assert "history_id" not in prediction.json()
    rows = ml_client.get("/api/history", params={"module": "fisioterapia"}).json()
    assert rows["total"] == before + 1
    assert rows["items"][0]["record_reference"] == "PAC-0001"


def test_vision_session_stores_only_derived_metadata(client):
    result = client.post("/api/history/vision-session", json={"movements": 3, "samples": 41, "joint": "leftKnee", "reference": "session_1"})
    assert result.status_code == 200, result.text
    item = result.json()
    assert item["analysis_type"] == "vision_session"
    assert "3 movimentos" in item["result_summary"]
    assert "frames" not in item
    assert client.post("/api/history/vision-session", json={"movements": 3, "samples": 41, "joint": "leftKnee", "reference": "session_1", "image": "secret"}).status_code == 422
