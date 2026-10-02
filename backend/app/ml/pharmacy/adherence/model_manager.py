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

from app.ml.pharmacy.adherence.feature_config import FEATURES
from app.ml.pharmacy.adherence.train import train_candidates
from app.models.pharmacy import PharmacyAdherencePatient
from app.schemas.pharmacy import ADHERENCE_COLUMNS
from app.services.physiotherapy_validation import DatasetError

MODEL_DIR = Path(os.getenv("MODELS_DIR", str(Path(__file__).resolve().parents[4] / "models"))) / "pharmacy" / "adherence"
LOCK = threading.RLock()
_bundle: dict | None = None


def training_frame(db: Session) -> pd.DataFrame:
    patients = db.scalars(select(PharmacyAdherencePatient).order_by(PharmacyAdherencePatient.patient_id)).all()
    return pd.DataFrame([{key: getattr(item, key) for key in ADHERENCE_COLUMNS} for item in patients], columns=ADHERENCE_COLUMNS)


def snapshot() -> dict:
    with LOCK:
        if _bundle is None:
            raise DatasetError("Modelo de adesão indisponível. Treine com o dataset sintético.", 409)
        return _bundle


def train_model(db: Session) -> dict:
    global _bundle
    with LOCK:
        version = f"{int(_bundle['metadata']['version'].split('.')[0]) + 1 if _bundle else 1}.0"
        bundle = train_candidates(training_frame(db), version)
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=MODEL_DIR) as directory:
            tmp = Path(directory)
            joblib.dump(bundle, tmp / "pharmacy_adherence_model.joblib", compress=3)
            (tmp / "model_metadata.json").write_text(json.dumps(bundle["metadata"], ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp / "model_metadata.json", MODEL_DIR / "model_metadata.json")
            os.replace(tmp / "pharmacy_adherence_model.joblib", MODEL_DIR / "pharmacy_adherence_model.joblib")
        _bundle = bundle
        logging.getLogger(__name__).info("Pharmacy adherence model trained, version %s", version)
        return bundle["metadata"]


def initialize_model(db: Session) -> None:
    global _bundle
    with LOCK:
        path = MODEL_DIR / "pharmacy_adherence_model.joblib"
        if path.exists():
            try:
                bundle = joblib.load(path)  # Only our own local artifact; never an uploaded file.
                if bundle["metadata"]["features"] != FEATURES or bundle["metadata"]["sklearn_version"] != sklearn.__version__:
                    raise ValueError("Artefato incompatível")
                _bundle = bundle
                logging.getLogger(__name__).info("Pharmacy adherence model loaded")
            except Exception:
                _bundle = None
                logging.getLogger(__name__).exception("Could not load pharmacy adherence model")
        else:
            train_model(db)


def info() -> dict:
    return {**snapshot()["metadata"], "status": "ready"}
