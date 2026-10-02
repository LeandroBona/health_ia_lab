import json
import os
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.data_generators.physiotherapy import export_dataset, generate_patients
from app.models.physiotherapy import ImportPreview, PhysiotherapyDataset, PhysiotherapyPatient
from app.schemas.physiotherapy import REQUIRED_COLUMNS
from app.services.physiotherapy_validation import DatasetError, read_file, validate_frame

DATASET_DIR = Path(os.getenv("DATASETS_DIR", str(Path(__file__).resolve().parents[3] / "datasets"))) / "fisioterapia"
DEFAULT_ID = "default-physiotherapy"
DATA_LOCK = threading.RLock()
PREVIEW_TTL = 1800


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def insert_patients(db: Session, rows: list[dict], dataset_id: str) -> int:
    count = 0
    for start in range(0, len(rows), 200):
        statement = insert(PhysiotherapyPatient).values([{**row, "dataset_id": dataset_id} for row in rows[start:start + 200]])
        result = db.execute(statement.on_conflict_do_nothing(index_elements=["patient_id"]))
        count += result.rowcount
    return count


def replace_default(db: Session, frame: pd.DataFrame, seed: int | None) -> dict:
    """Serialize local writes and restore exports if the DB transaction fails."""
    with DATA_LOCK:
        DATASET_DIR.mkdir(parents=True, exist_ok=True)
        filenames = ["pacientes_fisioterapia.csv", "pacientes_fisioterapia.xlsx"]
        backups = {name: (DATASET_DIR / name).read_bytes() if (DATASET_DIR / name).exists() else None for name in filenames}
        with tempfile.TemporaryDirectory(dir=DATASET_DIR) as staging:
            export_dataset(frame, Path(staging))
            try:
                db.execute(delete(PhysiotherapyPatient).where(PhysiotherapyPatient.dataset_id == DEFAULT_ID))
                dataset = db.get(PhysiotherapyDataset, DEFAULT_ID)
                if dataset is None:
                    dataset = PhysiotherapyDataset(id=DEFAULT_ID, name="Dataset educacional padrão", size=len(frame), seed=seed, created_at=timestamp())
                    db.add(dataset)
                dataset.size, dataset.seed, dataset.created_at = len(frame), seed, timestamp()
                db.flush()
                imported = insert_patients(db, frame.to_dict(orient="records"), DEFAULT_ID)
                for name in filenames:
                    os.replace(Path(staging) / name, DATASET_DIR / name)
                db.commit()
            except Exception:
                db.rollback()
                for name, content in backups.items():
                    path = DATASET_DIR / name
                    if content is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.write_bytes(content)
                raise
        return {"success": True, "total": len(frame), "imported": imported, "ignored": len(frame) - imported, "seed": seed}


def regenerate_dataset(db: Session, size: int = 1000, seed: int = 42) -> dict:
    return replace_default(db, generate_patients(size, seed), seed)


def initialize_dataset(db: Session) -> None:
    with DATA_LOCK:
        dataset = db.get(PhysiotherapyDataset, DEFAULT_ID)
        csv_path = DATASET_DIR / "pacientes_fisioterapia.csv"
        xlsx_path = DATASET_DIR / "pacientes_fisioterapia.xlsx"
        if dataset is None:
            existing = csv_path if csv_path.exists() else xlsx_path if xlsx_path.exists() else None
            if existing is not None:
                frame = read_file(existing.read_bytes(), existing.name)
                _, rows = validate_frame(frame, existing.name)
                replace_default(db, pd.DataFrame(rows), None)
            else:
                regenerate_dataset(db)
        elif not csv_path.exists() or not xlsx_path.exists():
            # Restore missing artifacts without changing existing patient records.
            if csv_path.exists() or xlsx_path.exists():
                path = csv_path if csv_path.exists() else xlsx_path
                _, rows = validate_frame(read_file(path.read_bytes(), path.name), path.name)
                export_dataset(pd.DataFrame(rows), DATASET_DIR)
            elif dataset.seed is not None:
                export_dataset(generate_patients(dataset.size, dataset.seed), DATASET_DIR)
            else:
                patients = db.scalars(select(PhysiotherapyPatient).where(PhysiotherapyPatient.dataset_id == DEFAULT_ID).order_by(PhysiotherapyPatient.patient_id)).all()
                export_dataset(pd.DataFrame([{col: getattr(patient, col) for col in REQUIRED_COLUMNS} for patient in patients], columns=REQUIRED_COLUMNS), DATASET_DIR)
        db.execute(delete(ImportPreview).where(ImportPreview.expires_at < time.time()))
        db.commit()


def dataset_info(db: Session) -> dict:
    dataset = db.get(PhysiotherapyDataset, DEFAULT_ID)
    return {"name": dataset.name, "size": dataset.size, "seed": dataset.seed, "created_at": dataset.created_at, "format": "Sintético", "area": "Fisioterapia"}


def create_preview(db: Session, content: bytes, filename: str) -> dict:
    frame = read_file(content, filename)
    metadata, rows = validate_frame(frame, filename)
    with DATA_LOCK:
        db.execute(delete(ImportPreview).where(ImportPreview.expires_at < time.time()))
        if db.scalar(select(func.count()).select_from(ImportPreview)) >= 20:
            raise DatasetError("Há muitas prévias pendentes. Conclua uma importação ou aguarde 30 minutos.", 429)
        existing = set(db.scalars(select(PhysiotherapyPatient.patient_id)).all())
        seen = set(existing)
        ignored = 0
        for row in rows:
            if row["patient_id"] in seen:
                ignored += 1
            seen.add(row["patient_id"])
        token = uuid.uuid4().hex
        expires_at = time.time() + PREVIEW_TTL
        db.add(ImportPreview(token=token, filename=filename, expires_at=expires_at, payload=json.dumps(rows)))
        db.commit()
    return {**metadata, "token": token, "expires_at": expires_at, "duplicates": ignored, "importable": len(rows) - ignored}


def confirm_import(db: Session, token: str) -> dict:
    with DATA_LOCK:
        # Atomic claim: a preview can only be confirmed once, including concurrent requests.
        preview = db.execute(delete(ImportPreview).where(ImportPreview.token == token, ImportPreview.expires_at > time.time()).returning(ImportPreview.payload, ImportPreview.filename)).first()
        if preview is None:
            db.rollback()
            raise DatasetError("Prévia expirada ou já importada. Valide o arquivo novamente.", 409)
        rows = json.loads(preview.payload)
        db.add(PhysiotherapyDataset(id=token, name=preview.filename, size=0, seed=None, created_at=timestamp()))
        db.flush()
        imported = insert_patients(db, rows, token)
        dataset = db.get(PhysiotherapyDataset, token)
        if imported:
            dataset.size = imported
        else:
            db.delete(dataset)
        db.commit()
    return {"success": True, "imported": imported, "ignored": len(rows) - imported, "total": len(rows)}
