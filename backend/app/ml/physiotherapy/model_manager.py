import json
import logging
import os
import tempfile
import threading
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.physiotherapy.feature_config import FEATURES
from app.ml.physiotherapy.train import train_candidates
from app.ml.physiotherapy.utils import dataset_fingerprint
from app.models.physiotherapy import PhysiotherapyPatient
from app.schemas.physiotherapy import REQUIRED_COLUMNS
from app.services.physiotherapy_dataset import DEFAULT_ID
from app.services.physiotherapy_validation import DatasetError

MODEL_DIR = Path(os.getenv("MODELS_DIR", str(Path(__file__).resolve().parents[3] / "models"))) / "physiotherapy"
TRAIN_LOCK = threading.Lock()
STATE_LOCK = threading.RLock()
_bundle: dict | None = None
_load_error: str | None = None


def training_frame(db: Session, source: str) -> pd.DataFrame:
    query = select(PhysiotherapyPatient).order_by(PhysiotherapyPatient.patient_id)
    if source == "default":
        query = query.where(PhysiotherapyPatient.dataset_id == DEFAULT_ID)
    return pd.DataFrame([{key: getattr(patient, key) for key in REQUIRED_COLUMNS} for patient in db.scalars(query)], columns=REQUIRED_COLUMNS)


def snapshot() -> dict:
    with STATE_LOCK:
        if _bundle is None:
            raise DatasetError(_load_error or "Ainda não há modelo treinado. Abra Modelo de IA e treine com os dados atuais.", 409)
        return _bundle


def persist(bundle: dict) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / "physiotherapy_model.joblib"
    metadata_path = MODEL_DIR / "model_metadata.json"
    previous_metadata = metadata_path.read_bytes() if metadata_path.exists() else None
    with tempfile.TemporaryDirectory(dir=MODEL_DIR) as folder:
        temporary = Path(folder)
        joblib.dump(bundle, temporary / model_path.name, compress=3)
        (temporary / metadata_path.name).write_text(json.dumps(bundle["metadata"], indent=2, ensure_ascii=False), encoding="utf-8")
        # Joblib is authoritative and contains matching metadata. Replace it atomically last.
        try:
            os.replace(temporary / metadata_path.name, metadata_path)
            os.replace(temporary / model_path.name, model_path)
        except Exception:
            if previous_metadata is not None:
                metadata_path.write_bytes(previous_metadata)
            else:
                metadata_path.unlink(missing_ok=True)
            raise


def train_model(db: Session, source: str = "database") -> dict:
    global _bundle, _load_error
    if not TRAIN_LOCK.acquire(blocking=False):
        raise DatasetError("Um treinamento já está em andamento. Aguarde sua conclusão.", 409)
    try:
        previous = _bundle["metadata"]["version"] if _bundle else "0.0"
        version = f"{int(previous.split('.')[0]) + 1}.0"
        bundle = train_candidates(training_frame(db, source), version, source)
        persist(bundle)
        with STATE_LOCK:
            _bundle, _load_error = bundle, None
        return {**bundle["metadata"], **{key: bundle["metadata"]["metrics"][key] for key in ["accuracy", "f1_macro"]}}
    finally:
        TRAIN_LOCK.release()


def initialize_model(db: Session) -> None:
    global _bundle, _load_error
    path = MODEL_DIR / "physiotherapy_model.joblib"
    if path.exists():
        try:
            # Only load our local artifact; uploads can never provide a joblib path.
            bundle = joblib.load(path)
            if bundle["metadata"]["features"] != FEATURES or bundle["metadata"]["sklearn_version"] != sklearn.__version__:
                raise ValueError("Versão de dependência ou features incompatíveis")
            with STATE_LOCK:
                _bundle, _load_error = bundle, None
            (MODEL_DIR / "model_metadata.json").write_text(json.dumps(bundle["metadata"], ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            _bundle = None
            _load_error = "O artefato salvo está indisponível ou incompatível. Treine novamente na página Modelo de IA."
            logging.getLogger(__name__).exception("Could not load local physiotherapy model")
    else:
        try:
            train_model(db, source="default")
        except DatasetError as exc:
            _load_error = str(exc.body["message"])
            logging.getLogger(__name__).warning("Model initialization: %s", _load_error)


def model_info(db: Session) -> dict:
    if _bundle is None:
        return {"status": "unavailable", "message": _load_error or "Nenhum modelo treinado."}
    metadata = snapshot()["metadata"]
    current = training_frame(db, metadata["dataset_source"])
    return {**metadata, "status": "ready", "training": TRAIN_LOCK.locked(), "dataset_changed": dataset_fingerprint(current) != metadata["dataset_fingerprint"], "current_records": len(current)}


def available_count() -> int:
    return int(_bundle is not None)
