import time
from datetime import datetime, timezone

import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.pharmacy.adherence.evaluate import evaluate_model
from app.ml.pharmacy.adherence.feature_config import CLASSES, FEATURES, NOTICE, SEED, TARGET
from app.ml.pharmacy.adherence.preprocessing import build_preprocessor
from app.services.physiotherapy_validation import DatasetError


def train_candidates(frame, version: str) -> dict:
    counts = frame[TARGET].value_counts()
    if len(frame) < 30 or any(counts.get(label, 0) < 5 for label in CLASSES):
        raise DatasetError("Treinamento requer ao menos 30 registros e cinco exemplos por categoria.")
    started = time.perf_counter()
    train, test = train_test_split(frame, test_size=0.2, stratify=frame[TARGET], random_state=SEED)
    candidates = {
        "LogisticRegression": Pipeline([("preprocessing", build_preprocessor(True)), ("classifier", LogisticRegression(max_iter=2000, random_state=SEED, class_weight="balanced"))]),
        "RandomForestClassifier": Pipeline([("preprocessing", build_preprocessor()), ("classifier", RandomForestClassifier(n_estimators=180, min_samples_leaf=2, random_state=SEED, class_weight="balanced", n_jobs=1))]),
    }
    metrics = {}
    for name, pipeline in candidates.items():
        pipeline.fit(train[FEATURES], train[TARGET])
        metrics[name] = evaluate_model(pipeline, test[FEATURES], test[TARGET])
    selected = max(metrics, key=lambda name: metrics[name]["f1_macro"])
    metadata = {
        "name": "Classificação educacional de adesão medicamentosa", "algorithm": selected,
        "version": version, "trained_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(frame), "training_samples": len(train), "test_samples": len(test),
        "features": FEATURES, "target": TARGET, "classes": CLASSES, "random_state": SEED,
        "metrics": metrics[selected], "algorithms": metrics, "selection_metric": "f1_macro",
        "training_seconds": round(time.perf_counter() - started, 3), "sklearn_version": sklearn.__version__,
        "educational_notice": NOTICE,
        "evaluation_note": "O conjunto de teste foi usado para comparar algoritmos; não é validação externa. adesao_percentual não entra nas features.",
    }
    return {"pipeline": candidates[selected], "metadata": metadata}
