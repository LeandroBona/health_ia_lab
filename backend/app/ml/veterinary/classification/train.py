from datetime import datetime, timezone

import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .evaluate import evaluate
from .feature_config import FEATURES, TARGET
from .preprocessing import preprocessor


def train_candidates(frame: pd.DataFrame, version: str = "1.0", seed: int = 42) -> dict:
    if len(frame) < 30 or frame[TARGET].nunique() < 3 or frame[TARGET].value_counts().min() < 2:
        raise ValueError("São necessários ao menos 30 registros e duas amostras de cada categoria.")
    x_train, x_test, y_train, y_test = train_test_split(frame[FEATURES], frame[TARGET], test_size=.2, stratify=frame[TARGET], random_state=42)
    algorithms = {"RandomForestClassifier": RandomForestClassifier(n_estimators=160, min_samples_leaf=3, random_state=seed, n_jobs=-1),
                  "LogisticRegression": LogisticRegression(max_iter=1500, random_state=seed)}
    results = {}
    fitted = {}
    for name, estimator in algorithms.items():
        pipeline = Pipeline([("preprocess", preprocessor()), ("model", estimator)])
        pipeline.fit(x_train, y_train)
        fitted[name] = pipeline
        results[name] = evaluate(y_test, pipeline.predict(x_test))
    selected = max(results, key=lambda name: results[name]["f1_macro"])
    metadata = {"version": version, "algorithm": selected, "date": datetime.now(timezone.utc).isoformat(),
                "features": FEATURES, "dataset": "animais_veterinaria", "records": len(frame), "seed": seed,
                "train_records": len(x_train), "test_records": len(x_test), "metrics": results[selected],
                "algorithms": results, "sklearn_version": sklearn.__version__,
                "evaluation_note": "Métricas de teste estratificado sobre dados sintéticos; sem validade veterinária."}
    return {"pipeline": fitted[selected], "metadata": metadata}
