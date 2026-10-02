"""Synthetic default dataset and validated, single-use spreadsheet imports."""
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.data_generators.psychology import COLUMNS, export_reports, generate_reports
from app.models.psychology import PsychologyDataset, PsychologyImportPreview, PsychologyRecord
from app.schemas.psychology import OPTIONAL_COLUMNS, REQUIRED_COLUMNS, RecordRow
from app.services.physiotherapy_validation import DatasetError, read_file

DATASET_DIR = Path(os.getenv("DATASETS_DIR", str(Path(__file__).resolve().parents[3] / "datasets"))) / "psicologia"
DEFAULT_ID = "default-psychology"


def validate_frame(frame: pd.DataFrame, filename: str) -> tuple[dict, list[dict]]:
    found = [str(column) for column in frame.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in found]
    extra = [column for column in found if column not in COLUMNS]
    if missing or extra:
        raise DatasetError("Confira as colunas. Colunas adicionais não são aceitas para evitar dados pessoais.", missing_columns=missing, extra_columns=extra)
    frame = frame[found].replace(r"^\s*$", None, regex=True)
    absent = {column: int(frame[column].isna().sum()) for column in found}
    rows, errors, seen = [], [], set()
    for line, raw in enumerate(frame.to_dict("records"), 2):
        values = {key: None if pd.isna(value) else value for key, value in raw.items()}
        try:
            row = RecordRow.model_validate(values).model_dump(mode="json")
            if row["record_id"] in seen:
                raise ValueError("identificador duplicado no arquivo")
            seen.add(row["record_id"])
            rows.append(row)
        except (ValidationError, ValueError) as exc:
            if len(errors) < 100:
                errors.append({"row": line, "message": str(exc)[:180]})
    if errors:
        raise DatasetError("Foram encontrados relatos inválidos. Corrija o arquivo e valide novamente.", errors=errors, invalid_rows=len(errors), missing_values=absent)
    return {"success": True, "filename": filename, "record_count": len(rows), "column_count": len(found), "columns": found,
            "detected_types": {column: str(frame[column].dtype) for column in found}, "missing_values": absent,
            "missing_total": sum(absent.values()), "average_text_length": round(sum(len(row["texto"]) for row in rows) / len(rows), 1),
            "themes": sorted({row["tema_principal"] for row in rows}), "preview": rows[:20]}, rows


def initialize_dataset(db: Session, seed: int = 42, size: int = 1000) -> None:
    csv = DATASET_DIR / "relatos_psicologia.csv"
    xlsx = DATASET_DIR / "relatos_psicologia.xlsx"
    if db.get(PsychologyDataset, DEFAULT_ID) is None:
        source = csv if csv.exists() else xlsx if xlsx.exists() else None
        frame = read_file(source.read_bytes(), source.name) if source else generate_reports(size, seed)
        _, rows = validate_frame(frame, source.name if source else csv.name)
        db.add(PsychologyDataset(id=DEFAULT_ID, name="Dataset sintético padrão", size=len(rows), seed=seed if source is None else None,
                                 created_at=datetime.now(timezone.utc).isoformat()))
        db.flush()
        for start in range(0, len(rows), 200):
            db.execute(insert(PsychologyRecord).values([{**row, "dataset_id": DEFAULT_ID} for row in rows[start:start+200]]).on_conflict_do_nothing(index_elements=["record_id"]))
        db.commit()
        export_reports(pd.DataFrame(rows, columns=COLUMNS), DATASET_DIR)
    elif not csv.exists() or not xlsx.exists():
        items = db.scalars(select(PsychologyRecord).where(PsychologyRecord.dataset_id == DEFAULT_ID).order_by(PsychologyRecord.record_id)).all()
        export_reports(pd.DataFrame([{column: getattr(item, column) for column in COLUMNS} for item in items], columns=COLUMNS), DATASET_DIR)
    db.execute(delete(PsychologyImportPreview).where(PsychologyImportPreview.expires_at < time.time()))
    db.commit()


def create_preview(db: Session, content: bytes, filename: str) -> dict:
    info, rows = validate_frame(read_file(content, filename), filename)
    known = set(db.scalars(select(PsychologyRecord.record_id)).all())
    duplicates = sum(row["record_id"] in known for row in rows)
    token = uuid.uuid4().hex
    expiry = time.time() + 1800
    db.add(PsychologyImportPreview(token=token, filename=filename, expires_at=expiry, payload=json.dumps(rows, ensure_ascii=False)))
    db.commit()
    return {**info, "token": token, "expires_at": expiry, "duplicates": duplicates, "importable": len(rows) - duplicates}


def confirm_import(db: Session, token: str) -> dict:
    preview = db.execute(delete(PsychologyImportPreview).where(PsychologyImportPreview.token == token,
                                                                  PsychologyImportPreview.expires_at > time.time()).returning(PsychologyImportPreview.payload, PsychologyImportPreview.filename)).first()
    if preview is None:
        db.rollback()
        raise DatasetError("Prévia expirada ou já importada. Valide novamente.", 409)
    rows = json.loads(preview.payload)
    db.add(PsychologyDataset(id=token, name=preview.filename, size=0, seed=None, created_at=datetime.now(timezone.utc).isoformat()))
    db.flush()
    imported = 0
    for start in range(0, len(rows), 200):
        imported += db.execute(insert(PsychologyRecord).values([{**row, "dataset_id": token} for row in rows[start:start+200]]).on_conflict_do_nothing(index_elements=["record_id"])).rowcount
    dataset = db.get(PsychologyDataset, token)
    if imported:
        dataset.size = imported
    else:
        db.delete(dataset)
    db.commit()
    return {"success": True, "imported": imported, "ignored": len(rows) - imported, "total": len(rows)}


def default_file(format_: str) -> Path:
    if format_ not in {"csv", "xlsx"}:
        raise DatasetError("Arquivo não encontrado.", 404)
    return DATASET_DIR / f"relatos_psicologia.{format_}"
