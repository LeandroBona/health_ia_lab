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

from app.ml.pharmacy.demand.features import FEATURES
from app.ml.pharmacy.demand.train import train_candidates
from app.models.pharmacy import PharmacyDemandRecord
from app.schemas.pharmacy import DEMAND_COLUMNS
from app.services.physiotherapy_validation import DatasetError

MODEL_DIR = Path(os.getenv("MODELS_DIR", str(Path(__file__).resolve().parents[4] / "models"))) / "pharmacy" / "demand"
LOCK = threading.RLock()
_bundle: dict | None = None


def training_frame(db: Session) -> pd.DataFrame:
    records = db.scalars(select(PharmacyDemandRecord).order_by(PharmacyDemandRecord.medication_id, PharmacyDemandRecord.period)).all()
    return pd.DataFrame([{key: getattr(item, key) for key in DEMAND_COLUMNS} for item in records], columns=DEMAND_COLUMNS)


def snapshot() -> dict:
    with LOCK:
        if _bundle is None:
            raise DatasetError("Modelo de demanda indisponível. Treine com o dataset sintético.", 409)
        return _bundle


def train_model(db: Session) -> dict:
    global _bundle
    with LOCK:
        version = f"{int(_bundle['metadata']['version'].split('.')[0]) + 1 if _bundle else 1}.0"
        bundle = train_candidates(training_frame(db), version)
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=MODEL_DIR) as directory:
            tmp = Path(directory)
            joblib.dump(bundle, tmp / "demand_model.joblib", compress=3)
            (tmp / "demand_model_metadata.json").write_text(json.dumps(bundle["metadata"], ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp / "demand_model_metadata.json", MODEL_DIR / "demand_model_metadata.json")
            os.replace(tmp / "demand_model.joblib", MODEL_DIR / "demand_model.joblib")
        _bundle = bundle
        logging.getLogger(__name__).info("Pharmacy demand model trained, version %s", version)
        return bundle["metadata"]


def initialize_model(db: Session) -> None:
    global _bundle
    with LOCK:
        path = MODEL_DIR / "demand_model.joblib"
        if path.exists():
            try:
                bundle = joblib.load(path)
                if bundle["metadata"]["features"] != FEATURES or bundle["metadata"]["sklearn_version"] != sklearn.__version__:
                    raise ValueError("Artefato incompatível")
                _bundle = bundle
                logging.getLogger(__name__).info("Pharmacy demand model loaded")
            except Exception:
                _bundle = None
                logging.getLogger(__name__).exception("Could not load pharmacy demand model")
        else:
            train_model(db)


def info() -> dict:
    return {**snapshot()["metadata"], "status": "ready"}
