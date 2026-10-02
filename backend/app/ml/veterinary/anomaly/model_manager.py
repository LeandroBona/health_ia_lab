import json
import os
import tempfile
import threading
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data_generators.veterinary_followup import FOLLOWUP_COLUMNS
from app.models.veterinary import VeterinaryFollowUp
from app.services.physiotherapy_validation import DatasetError
from .preprocessing import FEATURES
from .train import train_model as fit_model

MODEL_DIR = Path(os.getenv("MODELS_DIR", str(Path(__file__).resolve().parents[4] / "models"))) / "veterinary"
LOCK = threading.RLock()
_bundle: dict | None = None


def snapshot() -> dict:
    if _bundle is None:
        raise DatasetError("Modelo de anomalias veterinárias indisponível.", 409)
    return _bundle


def train_model(db: Session, seed: int = 42) -> dict:
    global _bundle
    with LOCK:
        records = db.scalars(select(VeterinaryFollowUp)).all()
        frame = pd.DataFrame([{key: getattr(item, key) for key in FOLLOWUP_COLUMNS} for item in records], columns=FOLLOWUP_COLUMNS)
        version = f"{int(_bundle['metadata']['version'].split('.')[0]) + 1 if _bundle else 1}.0"
        try:
            bundle = fit_model(frame, version, seed)
        except ValueError as exc:
            raise DatasetError(str(exc)) from None
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=MODEL_DIR) as temporary:
            path = Path(temporary)
            joblib.dump(bundle, path / "veterinary_anomaly_model.joblib", compress=3)
            (path / "anomaly_metadata.json").write_text(json.dumps(bundle["metadata"], ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(path / "veterinary_anomaly_model.joblib", MODEL_DIR / "veterinary_anomaly_model.joblib")
            os.replace(path / "anomaly_metadata.json", MODEL_DIR / "anomaly_metadata.json")
        _bundle = bundle
        return bundle["metadata"]


def initialize_model(db: Session) -> None:
    global _bundle
    path = MODEL_DIR / "veterinary_anomaly_model.joblib"
    if path.exists():
        try:
            loaded = joblib.load(path)
            if loaded["metadata"]["features"] == FEATURES and loaded["metadata"]["sklearn_version"] == sklearn.__version__:
                _bundle = loaded
                return
        except Exception:
            pass
    train_model(db)


def info() -> dict:
    return {**snapshot()["metadata"], "status": "ready"}
