def test_readiness_uses_metadata_and_does_not_run_predictions(client, monkeypatch):
    def fail(_):
        raise AssertionError("previsão não deve ser executada na checagem")
    monkeypatch.setattr("app.api.classroom.predict_physiotherapy", fail)
    response = client.get("/api/classroom/readiness")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["backend"] is True
    assert payload["database"] is True
    assert payload["vision"] == "browser"
    assert payload["llm"]["available"] is True


def test_scenarios_use_existing_records_and_have_empty_fallback(client, ml_client):
    history_before = ml_client.get("/api/history").json()["total"]
    response = ml_client.get("/api/classroom/scenarios")
    assert response.status_code == 200, response.text
    selected = response.json()
    assert selected["physiotherapy_patient_id"]
    assert ml_client.get(f"/api/fisioterapia/patients/{selected['physiotherapy_patient_id']}").status_code == 200
    assert selected["nursing_pattern_id"] is None
    assert ml_client.get("/api/history").json()["total"] == history_before


def test_local_vite_port_can_call_classroom_api(client):
    response = client.options(
        "/api/classroom/scenarios",
        headers={
            "Origin": "http://127.0.0.1:5174",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5174"
