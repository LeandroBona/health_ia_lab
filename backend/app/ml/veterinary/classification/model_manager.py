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

from app.data_generators.veterinary import ANIMAL_COLUMNS
from app.models.veterinary import VeterinaryAnimal
from app.services.physiotherapy_validation import DatasetError
from .feature_config import FEATURES
from .train import train_candidates

MODEL_DIR = Path(os.getenv("MODELS_DIR", str(Path(__file__).resolve().parents[4] / "models"))) / "veterinary"
LOCK = threading.RLock()
_bundle: dict | None = None


def training_frame(db: Session) -> pd.DataFrame:
    animals = db.scalars(select(VeterinaryAnimal).order_by(VeterinaryAnimal.animal_id)).all()
    return pd.DataFrame([{key: getattr(animal, key) for key in ANIMAL_COLUMNS} for animal in animals], columns=ANIMAL_COLUMNS)


def snapshot() -> dict:
    if _bundle is None:
        raise DatasetError("Modelo veterinário indisponível. Treine com o dataset sintético.", 409)
    return _bundle


def train_model(db: Session, seed: int = 42) -> dict:
    global _bundle
    with LOCK:
        version = f"{int(_bundle['metadata']['version'].split('.')[0]) + 1 if _bundle else 1}.0"
        try:
            bundle = train_candidates(training_frame(db), version, seed)
        except ValueError as exc:
            raise DatasetError(str(exc)) from None
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=MODEL_DIR) as temporary:
            path = Path(temporary)
            joblib.dump(bundle, path / "veterinary_model.joblib", compress=3)
            (path / "model_metadata.json").write_text(json.dumps(bundle["metadata"], ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(path / "veterinary_model.joblib", MODEL_DIR / "veterinary_model.joblib")
            os.replace(path / "model_metadata.json", MODEL_DIR / "model_metadata.json")
        _bundle = bundle
        return bundle["metadata"]


def initialize_model(db: Session) -> None:
    global _bundle
    path = MODEL_DIR / "veterinary_model.joblib"
    if path.exists():
        try:
            loaded = joblib.load(path)  # Generated locally; imports never load joblib files.
            if loaded["metadata"]["features"] == FEATURES and loaded["metadata"]["sklearn_version"] == sklearn.__version__:
                _bundle = loaded
                return
        except Exception:
            pass
    train_model(db)


def info() -> dict:
    return {**snapshot()["metadata"], "status": "ready"}
