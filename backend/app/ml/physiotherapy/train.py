import time
from datetime import datetime, timezone

import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.physiotherapy.evaluate import evaluate_model
from app.ml.physiotherapy.feature_config import CLASSES, FEATURES, MODEL_NOTICE, RANDOM_STATE, TARGET
from app.ml.physiotherapy.preprocessing import build_preprocessor
from app.ml.physiotherapy.utils import dataset_fingerprint, record_fingerprint
from app.services.physiotherapy_validation import DatasetError


def train_candidates(frame: pd.DataFrame, version: str, source: str) -> dict:
    # Este modelo foi treinado exclusivamente com dados sintéticos e relações artificialmente construídas para fins educacionais. Seus resultados não possuem validade clínica.
    counts = frame[TARGET].value_counts()
    if len(frame) < 30 or any(counts.get(label, 0) < 5 for label in CLASSES):
        raise DatasetError("Treinamento requer ao menos 30 registros válidos e 5 exemplos de cada resultado. Amplie o dataset sintético.")
    started = time.perf_counter()
    train, test = train_test_split(frame, test_size=.2, stratify=frame[TARGET], random_state=RANDOM_STATE)
    algorithms = {
        "RandomForestClassifier": Pipeline([
            ("preprocessing", build_preprocessor()),
            ("classifier", RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, class_weight="balanced", min_samples_leaf=2, n_jobs=1)),
        ]),
        "LogisticRegression": Pipeline([
            ("preprocessing", build_preprocessor(scale_numeric=True)),
            ("classifier", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE, class_weight="balanced")),
        ]),
    }
    evaluations = {}
    for name, pipeline in algorithms.items():
        pipeline.fit(train[FEATURES], train[TARGET])
        evaluations[name] = evaluate_model(pipeline, test[FEATURES], test[TARGET])
    # Tie-breaking is stable (RF appears first); selection uses macro F1, never accuracy alone.
    selected = max(evaluations, key=lambda name: evaluations[name]["f1_macro"])
    metadata = {
        "name": "Classificador educacional de Fisioterapia", "algorithm": selected, "selected_model": selected,
        "model_version": version, "version": version, "trained_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(frame), "training_samples": len(train), "test_samples": len(test),
        "features": FEATURES, "target": TARGET, "classes": CLASSES, "random_state": RANDOM_STATE,
        "dataset_source": source, "dataset_fingerprint": dataset_fingerprint(frame),
        "metrics": evaluations[selected], "algorithms": evaluations, "selection_metric": "f1_macro",
        "training_seconds": round(time.perf_counter() - started, 3), "sklearn_version": sklearn.__version__,
        "educational_notice": MODEL_NOTICE,
        "evaluation_note": "A divisão de teste também foi usada para selecionar o algoritmo. As métricas não constituem validação externa ou clínica. A pipeline salva foi ajustada apenas nos 80% de treino.",
    }
    return {
        "pipeline": algorithms[selected], "metadata": metadata,
        "explanation_background": train[FEATURES].sample(n=min(40, len(train)), random_state=RANDOM_STATE).to_dict(orient="records"),
        "explanation_test_sample": test[FEATURES].sample(n=min(60, len(test)), random_state=RANDOM_STATE).to_dict(orient="records"),
        "membership": {
            record["patient_id"]: {"partition": partition, "fingerprint": record_fingerprint(record)}
            for partition, subset in [("train", train), ("test", test)]
            for record in subset.to_dict(orient="records")
        },
    }
