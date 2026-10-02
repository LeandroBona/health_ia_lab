"""Dataset generation, validation, and two-step imports."""
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

from app.data_generators.veterinary import ANIMAL_COLUMNS, export_animals, generate_animals
from app.data_generators.veterinary_followup import FOLLOWUP_COLUMNS, export_followups, generate_followups
from app.models.veterinary import VeterinaryAnimal, VeterinaryDataset, VeterinaryFollowUp, VeterinaryImportPreview
from app.schemas.veterinary import AnimalRow, DATASET_COLUMNS, FollowUpRow
from app.services.physiotherapy_validation import DatasetError, read_file

DATASET_DIR = Path(os.getenv("DATASETS_DIR", str(Path(__file__).resolve().parents[3] / "datasets"))) / "veterinaria"
CONFIG = {"animals": (AnimalRow, VeterinaryAnimal, "animais_veterinaria", export_animals, "animal_id"),
          "followups": (FollowUpRow, VeterinaryFollowUp, "acompanhamento_veterinario", export_followups, "followup_id")}


def validate_frame(kind: str, frame: pd.DataFrame, filename: str) -> tuple[dict, list[dict]]:
    if kind not in CONFIG:
        raise DatasetError("Tipo de dataset não reconhecido.", 404)
    columns = DATASET_COLUMNS[kind]
    found = [str(column) for column in frame.columns]
    missing = [column for column in columns if column not in found]
    extra = [column for column in found if column not in columns]
    if missing or extra:
        raise DatasetError("Confira as colunas. Colunas adicionais não são aceitas para evitar dados pessoais.", missing_columns=missing, extra_columns=extra)
    frame = frame[columns].replace(r"^\s*$", None, regex=True)
    absent = {column: int(frame[column].isna().sum()) for column in columns}
    schema = CONFIG[kind][0]
    rows, errors, seen = [], [], set()
    key = CONFIG[kind][4]
    for line, raw in enumerate(frame.to_dict("records"), 2):
        data = {name: None if pd.isna(value) else value for name, value in raw.items()}
        try:
            row = schema.model_validate(data).model_dump(mode="json")
            if row[key] in seen:
                raise ValueError("identificador duplicado no arquivo")
            if kind == "followups":
                datetime.fromisoformat(row["timestamp"])
            seen.add(row[key])
            rows.append(row)
        except (ValidationError, ValueError) as exc:
            if len(errors) < 100:
                errors.append({"row": line, "message": str(exc)[:180]})
    if errors:
        raise DatasetError("Foram encontrados registros inválidos. Corrija o arquivo e valide novamente.", errors=errors, invalid_rows=len(errors), missing_values=absent)
    return {"success": True, "filename": filename, "record_count": len(rows), "column_count": len(columns), "columns": columns,
            "detected_types": {column: str(frame[column].dtype) for column in columns}, "missing_values": absent,
            "missing_total": sum(absent.values()), "preview": rows[:20]}, rows


def initialize_datasets(db: Session, seed: int = 42, size: int = 1000) -> None:
    animals = generate_animals(size, seed)
    followups = generate_followups(animals, seed)
    for kind, frame in (("animals", animals), ("followups", followups)):
        dataset_id = f"default-veterinary-{kind}"
        schema, model, basename, exporter, key = CONFIG[kind]
        csv = DATASET_DIR / f"{basename}.csv"
        xlsx = DATASET_DIR / f"{basename}.xlsx"
        if db.get(VeterinaryDataset, dataset_id) is None:
            source = csv if csv.exists() else xlsx if xlsx.exists() else None
            if source:
                frame = read_file(source.read_bytes(), source.name, max_rows=10000)
            _, rows = validate_frame(kind, frame, source.name if source else csv.name)
            db.add(VeterinaryDataset(id=dataset_id, kind=kind, name="Dataset educacional padrão", size=len(rows), seed=seed if source is None else None,
                                     created_at=datetime.now(timezone.utc).isoformat()))
            db.flush()
            if kind == "followups":
                known = set(db.scalars(select(VeterinaryAnimal.animal_id)).all())
                rows = [row for row in rows if row["animal_id"] in known]
            for start in range(0, len(rows), 200):
                db.execute(insert(model).values([{**row, "dataset_id": dataset_id} for row in rows[start:start+200]]).on_conflict_do_nothing(index_elements=[key]))
            db.commit()
            exporter(pd.DataFrame(rows, columns=DATASET_COLUMNS[kind]), DATASET_DIR)
        elif not csv.exists() or not xlsx.exists():
            stored = db.scalars(select(model).where(model.dataset_id == dataset_id).order_by(getattr(model, key))).all()
            exporter(pd.DataFrame([{col: getattr(item, col) for col in DATASET_COLUMNS[kind]} for item in stored]), DATASET_DIR)
    db.execute(delete(VeterinaryImportPreview).where(VeterinaryImportPreview.expires_at < time.time()))
    db.commit()


def create_preview(db: Session, kind: str, content: bytes, filename: str) -> dict:
    if kind not in CONFIG:
        raise DatasetError("Tipo de dataset não reconhecido.", 404)
    info, rows = validate_frame(kind, read_file(content, filename), filename)
    _, model, _, _, key = CONFIG[kind]
    known = set(db.scalars(select(getattr(model, key))).all())
    if kind == "followups":
        animal_ids = set(db.scalars(select(VeterinaryAnimal.animal_id)).all())
        absent = sorted({row["animal_id"] for row in rows} - animal_ids)
        if absent:
            raise DatasetError("Acompanhamentos referenciam animais não cadastrados.", missing_animals=absent[:20])
    token = uuid.uuid4().hex
    expiry = time.time() + 1800
    db.add(VeterinaryImportPreview(token=token, kind=kind, filename=filename, expires_at=expiry, payload=json.dumps(rows, ensure_ascii=False)))
    db.commit()
    duplicates = sum(row[key] in known for row in rows)
    return {**info, "token": token, "expires_at": expiry, "duplicates": duplicates, "importable": len(rows) - duplicates}


def confirm_import(db: Session, kind: str, token: str) -> dict:
    if kind not in CONFIG:
        raise DatasetError("Tipo de dataset não reconhecido.", 404)
    preview = db.execute(delete(VeterinaryImportPreview).where(VeterinaryImportPreview.token == token, VeterinaryImportPreview.kind == kind,
                                                                  VeterinaryImportPreview.expires_at > time.time()).returning(VeterinaryImportPreview.payload, VeterinaryImportPreview.filename)).first()
    if preview is None:
        db.rollback()
        raise DatasetError("Prévia expirada ou já importada. Valide novamente.", 409)
    rows = json.loads(preview.payload)
    _, model, _, _, key = CONFIG[kind]
    if kind == "followups":
        known = set(db.scalars(select(VeterinaryAnimal.animal_id)).all())
        if any(row["animal_id"] not in known for row in rows):
            db.rollback()
            raise DatasetError("A lista de animais mudou. Valide novamente.", 409)
    db.add(VeterinaryDataset(id=token, kind=kind, name=preview.filename, size=0, seed=None, created_at=datetime.now(timezone.utc).isoformat()))
    db.flush()
    imported = 0
    for start in range(0, len(rows), 200):
        imported += db.execute(insert(model).values([{**row, "dataset_id": token} for row in rows[start:start+200]]).on_conflict_do_nothing(index_elements=[key])).rowcount
    dataset = db.get(VeterinaryDataset, token)
    if imported:
        dataset.size = imported
    else:
        db.delete(dataset)
    db.commit()
    return {"success": True, "imported": imported, "ignored": len(rows) - imported, "total": len(rows)}


def default_file(kind: str, format_: str) -> Path:
    if kind not in CONFIG or format_ not in {"csv", "xlsx"}:
        raise DatasetError("Arquivo não encontrado.", 404)
    return DATASET_DIR / f"{CONFIG[kind][2]}.{format_}"
