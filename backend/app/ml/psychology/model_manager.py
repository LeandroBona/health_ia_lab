import json
import os
import tempfile
import threading
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data_generators.psychology import COLUMNS
from app.models.psychology import PsychologyRecord
from app.services.physiotherapy_validation import DatasetError
from .classification import train_classifier
from .preprocessing import PREPROCESSING_VERSION, make_vectorizer
from .clustering import cluster_summary

MODEL_DIR = Path(os.getenv("MODELS_DIR", str(Path(__file__).resolve().parents[3] / "models"))) / "psychology"
LOCK = threading.RLock()
_bundle: dict | None = None


def training_frame(db: Session) -> pd.DataFrame:
    items = db.scalars(select(PsychologyRecord).order_by(PsychologyRecord.record_id)).all()
    return pd.DataFrame([{key: getattr(item, key) for key in COLUMNS} for item in items], columns=COLUMNS)


def snapshot() -> dict:
    if _bundle is None:
        raise DatasetError("Modelo de NLP indisponível. Treine com o dataset sintético.", 409)
    return _bundle


def train_model(db: Session, seed: int = 42) -> dict:
    global _bundle
    with LOCK:
        frame = training_frame(db)
        version = f"{int(_bundle['metadata']['version'].split('.')[0]) + 1 if _bundle else 1}.0"
        try:
            classifier = train_classifier(frame, version, seed)
            vectorizer = make_vectorizer()
            matrix = vectorizer.fit_transform(frame.texto)
            kmeans = KMeans(n_clusters=5, n_init=10, random_state=seed)
            groups = kmeans.fit_predict(matrix)
        except ValueError as exc:
            raise DatasetError(str(exc)) from None
        metadata = classifier["metadata"]
        metadata.update({"cluster_count": 5, "cluster_algorithm": "TF-IDF + KMeans",
                         "similarity_algorithm": "TF-IDF + Similaridade de Cosseno", "features": int(matrix.shape[1]),
                         "preprocessing_version": PREPROCESSING_VERSION,
                         "cluster_sizes": {f"Grupo {index + 1}": int((groups == index).sum()) for index in range(5)}})
        bundle = {"pipeline": classifier["pipeline"], "vectorizer": vectorizer, "matrix": matrix,
                  "kmeans": kmeans, "clusters": groups, "records": frame[COLUMNS].to_dict("records"), "metadata": metadata}
        bundle["cluster_summary"] = cluster_summary(bundle)
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=MODEL_DIR) as temporary:
            path = Path(temporary)
            joblib.dump(bundle, path / "psychology_topic_model.joblib", compress=3)
            (path / "model_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(path / "psychology_topic_model.joblib", MODEL_DIR / "psychology_topic_model.joblib")
            os.replace(path / "model_metadata.json", MODEL_DIR / "model_metadata.json")
        _bundle = bundle
        return metadata


def initialize_model(db: Session) -> None:
    global _bundle
    path = MODEL_DIR / "psychology_topic_model.joblib"
    if path.exists():
        try:
            loaded = joblib.load(path)  # Locally generated artifact only; uploads cannot supply joblib files.
            if loaded["metadata"]["sklearn_version"] == sklearn.__version__ and loaded["metadata"]["input"] == ["texto"] and loaded["metadata"].get("preprocessing_version") == PREPROCESSING_VERSION:
                _bundle = loaded
                return
        except Exception:
            pass
    train_model(db)


def info() -> dict:
    return {**snapshot()["metadata"], "status": "ready"}
