"""Dataset lifecycle and two-step import for synthetic nursing records."""

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.data_generators.nursing import export_dataset, generate_measurements
from app.models.nursing import NursingDataset, NursingImportPreview, NursingMeasurement, NursingPatient
from app.schemas.nursing import MeasurementRow, REQUIRED_COLUMNS
from app.services.physiotherapy_validation import DatasetError, read_file

DATASET_DIR = Path(os.getenv("DATASETS_DIR", str(Path(__file__).resolve().parents[3] / "datasets"))) / "enfermagem"
DEFAULT_ID = "default-nursing"
LOCK = threading.RLock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_frame(frame: pd.DataFrame, filename: str) -> tuple[dict, list[dict]]:
    columns = [str(column) for column in frame.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    extra = [column for column in columns if column not in REQUIRED_COLUMNS]
    if missing or extra:
        raise DatasetError("Confira as colunas. Colunas extras não são aceitas para evitar dados pessoais.", missing_columns=missing, extra_columns=extra)
    frame = frame[REQUIRED_COLUMNS].replace(r"^\s*$", None, regex=True)
    absent = {column: int(frame[column].isna().sum()) for column in REQUIRED_COLUMNS}
    rows, errors, ages = [], [], {}
    invalid_count = 0
    seen_ids = set()
    for index, raw in enumerate(frame.to_dict(orient="records"), start=2):
        data = {key: None if pd.isna(value) else value for key, value in raw.items()}
        try:
            parsed = MeasurementRow.model_validate(data)
            row = parsed.model_dump(mode="json")
            if row["measurement_id"] in seen_ids:
                raise ValueError("measurement_id repetido no arquivo")
            seen_ids.add(row["measurement_id"])
            if row["patient_id"] in ages and ages[row["patient_id"]] != row["idade"]:
                raise ValueError("idade inconsistente para o mesmo patient_id")
            ages[row["patient_id"]] = row["idade"]
            rows.append(row)
        except (ValidationError, ValueError) as exc:
            invalid_count += 1
            if len(errors) < 100:
                fields = ", ".join(str(error["loc"][0]) if error["loc"] else "valores" for error in exc.errors()) if isinstance(exc, ValidationError) else str(exc)
                errors.append({"row": index, "message": f"Verifique tipo, faixa ou valor obrigatório: {fields}"})
    if errors:
        raise DatasetError("Foram encontrados registros inválidos. Corrija o arquivo e valide novamente.", errors=errors, invalid_rows=invalid_count, missing_values=absent, missing_total=sum(absent.values()))
    return {
        "success": True, "filename": filename, "record_count": len(rows), "column_count": len(columns),
        "columns": REQUIRED_COLUMNS, "detected_types": {col: "numérico" if col not in {"measurement_id", "patient_id", "timestamp", "estado"} else "texto/data" for col in REQUIRED_COLUMNS},
        "missing_values": absent, "missing_total": sum(absent.values()), "preview": rows[:20],
    }, rows


def _insert(db: Session, rows: list[dict], dataset_id: str) -> int:
    existing_ages = dict(db.execute(select(NursingPatient.patient_id, NursingPatient.idade)).all())
    for row in rows:
        if row["patient_id"] in existing_ages and existing_ages[row["patient_id"]] != row["idade"]:
            raise DatasetError(f"Idade inconsistente para {row['patient_id']} em relação ao banco.")
    new_patients = {row["patient_id"]: row["idade"] for row in rows if row["patient_id"] not in existing_ages}
    if new_patients:
        db.execute(insert(NursingPatient).values([{"patient_id": key, "idade": value} for key, value in new_patients.items()]).on_conflict_do_nothing(index_elements=["patient_id"]))
    imported = 0
    for start in range(0, len(rows), 200):
        batch = [{**row, "dataset_id": dataset_id} for row in rows[start:start + 200]]
        imported += db.execute(insert(NursingMeasurement).values(batch).on_conflict_do_nothing(index_elements=["measurement_id"])).rowcount
    return imported


def initialize_dataset(db: Session) -> None:
    with LOCK:
        csv = DATASET_DIR / "monitoramento_enfermagem.csv"
        xlsx = DATASET_DIR / "monitoramento_enfermagem.xlsx"
        if db.get(NursingDataset, DEFAULT_ID) is None:
            source = csv if csv.exists() else xlsx if xlsx.exists() else None
            frame = read_file(source.read_bytes(), source.name, max_rows=20000) if source else generate_measurements()
            _, rows = validate_frame(frame, source.name if source else csv.name)
            db.add(NursingDataset(id=DEFAULT_ID, name="Dataset educacional padrão", patient_count=len({r["patient_id"] for r in rows}), measurement_count=len(rows), seed=42 if source is None else None, created_at=now()))
            db.flush()
            _insert(db, rows, DEFAULT_ID)
            db.commit()
            export_dataset(pd.DataFrame(rows, columns=REQUIRED_COLUMNS), DATASET_DIR)
        elif not csv.exists() or not xlsx.exists():
            rows = [{col: getattr(item, col) for col in REQUIRED_COLUMNS} for item in db.scalars(select(NursingMeasurement).where(NursingMeasurement.dataset_id == DEFAULT_ID).order_by(NursingMeasurement.measurement_id))]
            export_dataset(pd.DataFrame(rows, columns=REQUIRED_COLUMNS), DATASET_DIR)
        db.execute(delete(NursingImportPreview).where(NursingImportPreview.expires_at < time.time()))
        db.commit()


def dataset_info(db: Session) -> dict:
    dataset = db.get(NursingDataset, DEFAULT_ID)
    return {"name": dataset.name, "patient_count": dataset.patient_count, "measurement_count": dataset.measurement_count, "seed": dataset.seed, "created_at": dataset.created_at, "format": "Sintético", "area": "Enfermagem", "columns": REQUIRED_COLUMNS}


def create_preview(db: Session, content: bytes, filename: str) -> dict:
    frame = read_file(content, filename, max_rows=20000)
    metadata, rows = validate_frame(frame, filename)
    with LOCK:
        db.execute(delete(NursingImportPreview).where(NursingImportPreview.expires_at < time.time()))
        if db.scalar(select(func.count()).select_from(NursingImportPreview)) >= 20:
            raise DatasetError("Há muitas prévias pendentes. Aguarde ou conclua uma importação.", 429)
        existing = set(db.scalars(select(NursingMeasurement.measurement_id)).all())
        ages = dict(db.execute(select(NursingPatient.patient_id, NursingPatient.idade)).all())
        conflicts = sorted({row["patient_id"] for row in rows if row["patient_id"] in ages and ages[row["patient_id"]] != row["idade"]})
        if conflicts:
            raise DatasetError("A idade de um paciente já existente difere do arquivo.", conflicting_patients=conflicts[:20])
        ignored = sum(row["measurement_id"] in existing for row in rows)
        token = uuid.uuid4().hex
        expiry = time.time() + 1800
        db.add(NursingImportPreview(token=token, filename=filename, expires_at=expiry, payload=json.dumps(rows)))
        db.commit()
    return {**metadata, "token": token, "expires_at": expiry, "duplicates": ignored, "importable": len(rows) - ignored}


def confirm_import(db: Session, token: str) -> dict:
    with LOCK:
        preview = db.execute(delete(NursingImportPreview).where(NursingImportPreview.token == token, NursingImportPreview.expires_at > time.time()).returning(NursingImportPreview.payload, NursingImportPreview.filename)).first()
        if preview is None:
            db.rollback()
            raise DatasetError("Prévia expirada ou já importada. Valide novamente.", 409)
        rows = json.loads(preview.payload)
        try:
            existing_ids = set(db.scalars(select(NursingMeasurement.measurement_id)).all())
            db.add(NursingDataset(id=token, name=preview.filename, patient_count=0, measurement_count=0, seed=None, created_at=now()))
            db.flush()
            imported = _insert(db, rows, token)
            dataset = db.get(NursingDataset, token)
            if imported:
                dataset.measurement_count = imported
                dataset.patient_count = len({row["patient_id"] for row in rows if row["measurement_id"] not in existing_ids})
            else:
                db.delete(dataset)
            db.commit()
        except Exception:
            db.rollback()
            raise
    return {"success": True, "imported": imported, "ignored": len(rows) - imported, "total": len(rows)}
