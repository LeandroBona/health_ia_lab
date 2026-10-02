"""Synthetic Pharmacy datasets and safe two-step spreadsheet imports."""

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

from app.data_generators.pharmacy_adherence import export_adherence, generate_adherence
from app.data_generators.pharmacy_demand import export_demand, generate_demand
from app.models.pharmacy import PharmacyAdherencePatient, PharmacyDataset, PharmacyDemandRecord, PharmacyImportPreview
from app.schemas.pharmacy import ADHERENCE_COLUMNS, DEMAND_COLUMNS, AdherenceRow, DemandRow
from app.services.physiotherapy_validation import DatasetError, read_file

DATASET_DIR = Path(os.getenv("DATASETS_DIR", str(Path(__file__).resolve().parents[3] / "datasets"))) / "farmacia"
KINDS = {"adesao": (ADHERENCE_COLUMNS, AdherenceRow, PharmacyAdherencePatient, "adesao_farmacia", export_adherence), "demanda": (DEMAND_COLUMNS, DemandRow, PharmacyDemandRecord, "demanda_farmacia", export_demand)}
LOCK = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_frame(kind: str, frame: pd.DataFrame, filename: str) -> tuple[dict, list[dict]]:
    if kind not in KINDS:
        raise DatasetError("Tipo de dataset não reconhecido.", 404)
    columns, schema, _, _, _ = KINDS[kind]
    found = [str(col) for col in frame.columns]
    missing = [col for col in columns if col not in found]
    extra = [col for col in found if col not in columns]
    if missing or extra:
        raise DatasetError("Confira as colunas. Colunas adicionais não são aceitas para evitar dados pessoais.", missing_columns=missing, extra_columns=extra)
    frame = frame[columns].replace(r"^\s*$", None, regex=True)
    absent = {col: int(frame[col].isna().sum()) for col in columns}
    rows, errors = [], []
    for line, raw in enumerate(frame.to_dict(orient="records"), 2):
        data = {key: None if pd.isna(value) else value for key, value in raw.items()}
        try:
            rows.append(schema.model_validate(data).model_dump(mode="json"))
        except ValidationError as exc:
            if len(errors) < 100:
                fields = ", ".join(str(error["loc"][0]) if error["loc"] else "registro" for error in exc.errors())
                errors.append({"row": line, "message": f"Verifique tipo, faixa ou relação entre valores: {fields}"})
    if errors:
        raise DatasetError("Foram encontrados registros inválidos. Corrija o arquivo e valide novamente.", errors=errors, invalid_rows=len(errors), missing_columns=[], missing_values=absent)
    return {"success": True, "filename": filename, "record_count": len(rows), "column_count": len(columns), "columns": columns, "detected_types": {col: str(frame[col].dtype) for col in columns}, "missing_values": absent, "missing_total": sum(absent.values()), "preview": rows[:20]}, rows


def _key(kind: str, row: dict) -> str | tuple[str, str]:
    return row["patient_id"] if kind == "adesao" else (row["medication_id"], row["period"])


def _existing_keys(db: Session, kind: str) -> set:
    if kind == "adesao":
        return set(db.scalars(select(PharmacyAdherencePatient.patient_id)).all())
    return set(db.execute(select(PharmacyDemandRecord.medication_id, PharmacyDemandRecord.period)).all())


def _insert(db: Session, kind: str, rows: list[dict], dataset_id: str) -> int:
    _, _, model, _, _ = KINDS[kind]
    imported = 0
    seen = set()
    for start in range(0, len(rows), 200):
        unique = []
        for row in rows[start:start + 200]:
            key = _key(kind, row)
            if key not in seen:
                unique.append({**row, "dataset_id": dataset_id})
                seen.add(key)
        if unique:
            conflict = ["patient_id"] if kind == "adesao" else ["medication_id", "period"]
            imported += db.execute(insert(model).values(unique).on_conflict_do_nothing(index_elements=conflict)).rowcount
    return imported


def initialize_datasets(db: Session) -> None:
    with LOCK:
        for kind in KINDS:
            columns, _, model, basename, exporter = KINDS[kind]
            dataset_id = f"default-pharmacy-{kind}"
            csv, xlsx = DATASET_DIR / f"{basename}.csv", DATASET_DIR / f"{basename}.xlsx"
            if db.get(PharmacyDataset, dataset_id) is None:
                source = csv if csv.exists() else xlsx if xlsx.exists() else None
                frame = read_file(source.read_bytes(), source.name, max_rows=10000) if source else generate_adherence() if kind == "adesao" else generate_demand()
                _, rows = validate_frame(kind, frame, source.name if source else csv.name)
                db.add(PharmacyDataset(id=dataset_id, kind=kind, name="Dataset educacional padrão", size=len(rows), seed=42 if source is None else None, created_at=_now()))
                db.flush()
                _insert(db, kind, rows, dataset_id)
                db.commit()
                exporter(pd.DataFrame(rows, columns=columns), DATASET_DIR)
            elif not csv.exists() or not xlsx.exists():
                query = select(model).where(model.dataset_id == dataset_id)
                if kind == "adesao":
                    query = query.order_by(model.patient_id)
                else:
                    query = query.order_by(model.medication_id, model.period)
                rows = [{col: getattr(item, col) for col in columns} for item in db.scalars(query)]
                exporter(pd.DataFrame(rows, columns=columns), DATASET_DIR)
        db.execute(delete(PharmacyImportPreview).where(PharmacyImportPreview.expires_at < time.time()))
        db.commit()


def create_preview(db: Session, kind: str, content: bytes, filename: str) -> dict:
    frame = read_file(content, filename, max_rows=10000)
    metadata, rows = validate_frame(kind, frame, filename)
    with LOCK:
        db.execute(delete(PharmacyImportPreview).where(PharmacyImportPreview.expires_at < time.time()))
        if db.scalar(select(func.count()).select_from(PharmacyImportPreview)) >= 20:
            raise DatasetError("Há muitas prévias pendentes. Aguarde ou conclua uma importação.", 429)
        existing = _existing_keys(db, kind)
        seen = set(existing)
        ignored = 0
        for row in rows:
            key = _key(kind, row)
            ignored += key in seen
            seen.add(key)
        token = uuid.uuid4().hex
        expiry = time.time() + 1800
        db.add(PharmacyImportPreview(token=token, kind=kind, filename=filename, expires_at=expiry, payload=json.dumps(rows)))
        db.commit()
    return {**metadata, "token": token, "expires_at": expiry, "duplicates": ignored, "importable": len(rows) - ignored}


def confirm_import(db: Session, kind: str, token: str) -> dict:
    with LOCK:
        preview = db.execute(delete(PharmacyImportPreview).where(PharmacyImportPreview.token == token, PharmacyImportPreview.kind == kind, PharmacyImportPreview.expires_at > time.time()).returning(PharmacyImportPreview.payload, PharmacyImportPreview.filename)).first()
        if preview is None:
            db.rollback()
            raise DatasetError("Prévia expirada ou já importada. Valide novamente.", 409)
        rows = json.loads(preview.payload)
        db.add(PharmacyDataset(id=token, kind=kind, name=preview.filename, size=0, seed=None, created_at=_now()))
        db.flush()
        imported = _insert(db, kind, rows, token)
        dataset = db.get(PharmacyDataset, token)
        if imported:
            dataset.size = imported
        else:
            db.delete(dataset)
        db.commit()
    return {"success": True, "imported": imported, "ignored": len(rows) - imported, "total": len(rows)}


def default_file(kind: str, format_: str) -> Path:
    if kind not in KINDS or format_ not in {"csv", "xlsx"}:
        raise DatasetError("Arquivo não encontrado.", 404)
    return DATASET_DIR / f"{KINDS[kind][3]}.{format_}"
