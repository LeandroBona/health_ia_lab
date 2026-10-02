"""Persisted Isolation Forest artifact and on-demand/whole-dataset analysis."""

import json
import logging
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.nursing.evaluate import evaluate_labels
from app.ml.nursing.predict import predict_many, predict_one
from app.ml.nursing.train import fit_model
from app.models.nursing import NursingAnalysisRun, NursingMeasurement
from app.schemas.nursing import FEATURES
from app.services.physiotherapy_validation import DatasetError

MODEL_DIR = Path(os.getenv("MODELS_DIR", str(Path(__file__).resolve().parents[3] / "models"))) / "nursing"
LOCK = threading.RLock()
_bundle: dict | None = None


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def measurements_frame(db: Session) -> pd.DataFrame:
    items = db.scalars(select(NursingMeasurement).order_by(NursingMeasurement.measurement_id)).all()
    return pd.DataFrame([{**{feature: getattr(item, feature) for feature in FEATURES}, "measurement_id": item.measurement_id, "estado": item.estado} for item in items])


def snapshot() -> dict:
    with LOCK:
        if _bundle is None:
            raise DatasetError("Modelo de Enfermagem indisponível. Treine o modelo para analisar os registros.", 409)
        return _bundle


def _persist(bundle: dict) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=MODEL_DIR) as folder:
        tmp = Path(folder)
        joblib.dump(bundle, tmp / "nursing_isolation_forest.joblib", compress=3)
        (tmp / "model_metadata.json").write_text(json.dumps(bundle["metadata"], ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp / "model_metadata.json", MODEL_DIR / "model_metadata.json")
        os.replace(tmp / "nursing_isolation_forest.joblib", MODEL_DIR / "nursing_isolation_forest.joblib")


def train_model(db: Session, seed: int = 42, contamination: float = .07) -> dict:
    global _bundle
    with LOCK:
        frame = measurements_frame(db)
        if len(frame) < 20:
            raise DatasetError("São necessárias pelo menos 20 medições para treinar o modelo.")
        previous = _bundle["metadata"]["version"] if _bundle else "0.0"
        version = f"{int(previous.split('.')[0]) + 1}.0"
        pipeline = fit_model(frame, seed, contamination)
        results = predict_many(pipeline, frame)
        evaluation = evaluate_labels(frame["estado"].tolist(), [r["classification"] for r in results])
        metadata = {
            "name": "Detecção de Anomalias — Enfermagem", "algorithm": "IsolationForest", "version": version,
            "trained_at": now(), "training_records": len(frame), "features": FEATURES,
            "contamination": contamination, "seed": seed, "sklearn_version": sklearn.__version__,
            "statistics": {"artificial_anomalies": evaluation["artificial_anomalies"], "detected_anomalies": evaluation["detected_anomalies"]},
            "evaluation": evaluation,
        }
        bundle = {"pipeline": pipeline, "metadata": metadata}
        _persist(bundle)
        _bundle = bundle
        logging.getLogger(__name__).info("Nursing model trained: version %s, %d records", version, len(frame))
        analyze_all(db)
        return metadata


def initialize_model(db: Session) -> None:
    global _bundle
    with LOCK:
        path = MODEL_DIR / "nursing_isolation_forest.joblib"
        if path.exists():
            try:
                bundle = joblib.load(path)
                metadata = bundle["metadata"]
                if metadata["features"] != FEATURES or metadata["sklearn_version"] != sklearn.__version__:
                    raise ValueError("Features ou versão do scikit-learn incompatíveis")
                _bundle = bundle
                logging.getLogger(__name__).info("Nursing model loaded: version %s", metadata["version"])
            except Exception:
                _bundle = None
                logging.getLogger(__name__).exception("Could not load local nursing model")
        else:
            train_model(db)
        if _bundle is not None:
            version = _bundle["metadata"]["version"]
            stale = db.scalar(select(func.count()).select_from(NursingMeasurement).where((NursingMeasurement.analyzed_model_version != version) | NursingMeasurement.analyzed_model_version.is_(None)))
            if stale:
                analyze_all(db)


def analyze_all(db: Session) -> dict:
    with LOCK:
        bundle = snapshot()
        frame = measurements_frame(db)
        results = predict_many(bundle["pipeline"], frame)
        version = bundle["metadata"]["version"]
        for start in range(0, len(results), 500):
            batch = [
                {"measurement_id": frame.iloc[index]["measurement_id"], "classification": results[index]["classification"], "anomaly_score": results[index]["score"], "analyzed_model_version": version}
                for index in range(start, min(start + 500, len(results)))
            ]
            db.bulk_update_mappings(NursingMeasurement, batch)
        run = db.get(NursingAnalysisRun, "latest")
        if run is None:
            run = NursingAnalysisRun(id="latest", analyzed_at=now(), model_version=version, measurement_count=0, anomaly_count=0)
            db.add(run)
        run.analyzed_at = now()
        run.model_version = version
        run.measurement_count = len(results)
        run.anomaly_count = sum(r["classification"] == "anomalia" for r in results)
        db.commit()
        logging.getLogger(__name__).info("Nursing analysis executed: %d anomalies in %d measurements", run.anomaly_count, len(results))
        return {"success": True, "total": len(results), "anomalies": run.anomaly_count, "analyzed_at": run.analyzed_at, "model_version": version}


def model_info() -> dict:
    if _bundle is None:
        return {"status": "unavailable", "message": "Modelo não disponível."}
    return {**snapshot()["metadata"], "status": "ready"}


def predict_signals(signals: dict) -> dict:
    result = predict_one(snapshot()["pipeline"], signals)
    return {**result, "model_version": snapshot()["metadata"]["version"], "explanation": "O índice é uma distância matemática do padrão aprendido; não representa risco ou gravidade."}
