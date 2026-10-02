import io
import time

import pandas as pd
import pytest
from sqlalchemy import func, select

from app.data_generators.physiotherapy import generate_patients
from app.models.physiotherapy import ImportPreview, PhysiotherapyPatient
from app.schemas.physiotherapy import PatientData, REQUIRED_COLUMNS
from app.services import physiotherapy_dataset as datasets

PREFIX = "/api/fisioterapia"


def encoded(frame, extension="csv"):
    if extension == "csv":
        return frame.to_csv(index=False).encode("utf-8")
    buffer = io.BytesIO()
    frame.to_excel(buffer, index=False)
    return buffer.getvalue()


def preview(client, frame, extension="csv", path="/upload/preview"):
    return client.post(PREFIX + path, files={"file": (f"synthetic.{extension}", encoded(frame, extension))})


def confirm(client, token):
    return client.post(PREFIX + "/upload/confirm", json={"token": token})


def test_generator_reproducibility_contract_and_ranges():
    frame = generate_patients()
    assert len(frame) == 1000
    assert list(frame.columns) == REQUIRED_COLUMNS
    assert frame.patient_id.is_unique
    assert frame.patient_id.iloc[0] == "PAC-0001"
    assert frame.patient_id.iloc[-1] == "PAC-1000"
    pd.testing.assert_frame_equal(frame, generate_patients(seed=42))
    assert not frame.equals(generate_patients(seed=43))
    for row in frame.to_dict("records"):
        PatientData.model_validate(row)
    assert (frame.sessoes_realizadas + frame.faltas <= frame.sessoes_previstas).all()
    assert frame.adesao_exercicios.corr(frame.indice_funcional_atual - frame.indice_funcional_inicial) > .3
    assert set(frame.resultado) == {"recuperacao_adequada", "recuperacao_lenta", "abandono"}


def test_startup_files_idempotence_and_restore(client):
    csv_path = datasets.DATASET_DIR / "pacientes_fisioterapia.csv"
    xlsx_path = datasets.DATASET_DIR / "pacientes_fisioterapia.xlsx"
    assert csv_path.exists() and xlsx_path.exists()
    pd.testing.assert_frame_equal(pd.read_csv(csv_path), pd.read_excel(xlsx_path))
    modified = csv_path.stat().st_mtime_ns
    with client.test_sessions() as db:
        datasets.initialize_dataset(db)
        assert db.scalar(select(func.count()).select_from(PhysiotherapyPatient)) == 1000
    assert csv_path.stat().st_mtime_ns == modified
    xlsx_path.unlink()
    with client.test_sessions() as db:
        datasets.initialize_dataset(db)
    assert xlsx_path.exists()


def test_pagination_search_filters_detail(client):
    first = client.get(PREFIX + "/patients", params={"page": 1, "page_size": 20}).json()
    second = client.get(PREFIX + "/patients", params={"page": 2, "page_size": 20}).json()
    assert first["total"] == 1000 and first["total_pages"] == 50 and len(first["items"]) == 20
    assert {row["patient_id"] for row in first["items"]}.isdisjoint({row["patient_id"] for row in second["items"]})
    row = first["items"][0]
    found = client.get(PREFIX + "/patients", params={"search": "pac-0001"}).json()
    assert found["total"] == 1
    for key in ["resultado", "tipo_lesao", "sexo"]:
        filtered = client.get(PREFIX + "/patients", params={key: row[key]}).json()
        assert filtered["total"] > 0
        assert all(patient[key] == row[key] for patient in filtered["items"])
    combined = client.get(PREFIX + "/patients", params={key: row[key] for key in ["resultado", "tipo_lesao", "sexo"]}).json()
    assert all(all(patient[key] == row[key] for key in ["resultado", "tipo_lesao", "sexo"]) for patient in combined["items"])
    assert client.get(PREFIX + "/patients/PAC-0001").json() == row
    assert client.get(PREFIX + "/patients/PAC-9999").status_code == 404
    assert client.get(PREFIX + "/patients", params={"search": "%"}).json()["total"] == 0
    assert client.get(PREFIX + "/patients?page=0").status_code == 422
    assert client.get(PREFIX + "/patients?page_size=101").status_code == 422
    assert client.get(PREFIX + "/patients?sexo=inexistente").status_code == 422


@pytest.mark.parametrize("extension", ["csv", "xlsx"])
def test_upload_preview_confirmation_duplicates(client, extension):
    frame = generate_patients(3)
    frame.loc[1, "patient_id"] = "PAC-9001"
    frame.loc[2, "patient_id"] = "PAC-9001"
    response = preview(client, frame, extension)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["record_count"] == 3 and data["column_count"] == 18
    assert data["missing_total"] == 0 and data["duplicates"] == 2
    assert len(data["preview"]) == 3 and len(data["detected_types"]) == 18
    assert client.get(PREFIX + "/stats").json()["total_patients"] == 1000
    result = confirm(client, data["token"])
    assert result.json() == {"success": True, "imported": 1, "ignored": 2, "total": 3}
    assert confirm(client, data["token"]).status_code == 409
    assert client.get(PREFIX + "/stats").json()["total_patients"] == 1001
    assert client.get("/api/dashboard").json()["datasets"] == 2


def test_upload_alias_only_previews_and_limit(client):
    data = preview(client, generate_patients(30), path="/upload").json()
    assert len(data["preview"]) == 20
    assert client.get(PREFIX + "/stats").json()["total_patients"] == 1000
    result = confirm(client, data["token"]).json()
    assert result["imported"] == 0 and result["ignored"] == 30
    assert client.get("/api/dashboard").json()["datasets"] == 1


@pytest.mark.parametrize("filename,content,status", [("bad.txt", b"text", 415), ("bad.xlsx", b"not excel", 422), ("bad.csv", b"", 422), ("big.csv", b"x" * (5 * 1024 * 1024 + 1), 413)])
def test_invalid_files(client, filename, content, status):
    response = client.post(PREFIX + "/upload/preview", files={"file": (filename, content)})
    assert response.status_code == status
    assert response.json()["success"] is False
    assert "Traceback" not in response.text


def test_missing_and_extra_columns(client):
    frame = generate_patients(1).drop(columns=["adesao_exercicios"])
    response = preview(client, frame)
    assert response.status_code == 422
    assert response.json()["missing_columns"] == ["adesao_exercicios"]
    frame = generate_patients(1).assign(email="synthetic@example.invalid")
    assert preview(client, frame).json()["extra_columns"] == ["email"]


@pytest.mark.parametrize("column,value", [("idade", 17), ("idade", 86), ("dor_atual", 11), ("mobilidade_atual", -1), ("forca_muscular", 0), ("comorbidades", 6), ("sessoes_realizadas", 31), ("faltas", 30), ("adesao_exercicios", 101), ("idade", "texto"), ("idade", 20.5), ("idade", None), ("sexo", "inválido"), ("resultado", "previsto"), ("patient_id", "nome de pessoa")])
def test_invalid_values(client, column, value):
    frame = generate_patients(1).astype(object)
    frame.loc[0, column] = value
    response = preview(client, frame)
    assert response.status_code == 422, response.text
    assert response.json()["errors"][0]["row"] == 2
    assert client.get(PREFIX + "/stats").json()["total_patients"] == 1000


def test_expiry_and_confirmation_payload(client):
    token = preview(client, generate_patients(1)).json()["token"]
    with client.test_sessions() as db:
        db.get(ImportPreview, token).expires_at = time.time() - 1
        db.commit()
    assert confirm(client, token).status_code == 409
    assert confirm(client, "../../file.csv").status_code == 422


def test_stats_exploration_downloads_dashboard(client):
    frame = generate_patients()
    stats = client.get(PREFIX + "/stats").json()
    assert stats["average_age"] == round(frame.idade.mean(), 1)
    assert sum(stats["results"].values()) == stats["total_patients"] == 1000
    assert sum(row["count"] for row in stats["adherence_distribution"]) == 1000
    assert sum(row["count"] for row in stats["injuries"]) == 1000
    exploration = client.get(PREFIX + "/explore?column=idade").json()
    assert exploration["median"] == frame.idade.median()
    assert exploration["std"] == round(frame.idade.std(ddof=0), 2)
    assert sum(row["count"] for row in exploration["distribution"]) == 1000
    assert client.get(PREFIX + "/explore?column=sexo").json()["kind"] == "categorical"
    assert client.get(PREFIX + "/explore?column=patient_id").json()["truncated"] is True
    assert client.get(PREFIX + "/explore?column=invalid").status_code == 422
    for extension in ["csv", "xlsx"]:
        response = client.get(PREFIX + f"/dataset/download/{extension}")
        assert response.status_code == 200 and len(response.content) > 1000
    assert client.get(PREFIX + "/dataset/download/db").status_code == 404
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["patients"] == 1000 and dashboard["datasets"] == 1 and dashboard["models"] == 0


def test_regeneration_preserves_imports_and_is_reproducible(client):
    frame = generate_patients(1)
    frame.loc[0, "patient_id"] = "PAC-9001"
    confirm(client, preview(client, frame).json()["token"])
    assert client.post(PREFIX + "/dataset/regenerate", json={"size": 40}).status_code == 409
    result = client.post(PREFIX + "/dataset/regenerate", json={"size": 40, "seed": 9, "confirm": True})
    assert result.status_code == 200
    assert client.get(PREFIX + "/stats").json()["total_patients"] == 41
    assert client.get(PREFIX + "/patients/PAC-9001").status_code == 200
    pd.testing.assert_frame_equal(pd.read_csv(datasets.DATASET_DIR / "pacientes_fisioterapia.csv"), generate_patients(40, 9))
    assert client.get(PREFIX + "/dataset").json()["seed"] == 9


def test_failed_export_does_not_change_database(client, monkeypatch):
    def fail(*args):
        raise OSError("simulated write failure")
    before = (datasets.DATASET_DIR / "pacientes_fisioterapia.csv").read_bytes()
    monkeypatch.setattr(datasets, "export_dataset", fail)
    with pytest.raises(OSError):
        with client.test_sessions() as db:
            datasets.regenerate_dataset(db, 20, 1)
    assert client.get(PREFIX + "/stats").json()["total_patients"] == 1000
    assert (datasets.DATASET_DIR / "pacientes_fisioterapia.csv").read_bytes() == before
