from datetime import datetime, timezone

import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline

from .preprocessing import FEATURES, preprocessor


def train_model(frame: pd.DataFrame, version: str = "1.0", seed: int = 42) -> dict:
    if len(frame) < 30:
        raise ValueError("São necessários ao menos 30 acompanhamentos.")
    pipeline = Pipeline([("preprocess", preprocessor()), ("model", IsolationForest(n_estimators=160, contamination=.07, random_state=seed, n_jobs=-1))])
    pipeline.fit(frame[FEATURES])
    labels = pipeline.predict(frame[FEATURES])
    metadata = {"version": version, "algorithm": "IsolationForest", "date": datetime.now(timezone.utc).isoformat(),
                "features": FEATURES, "dataset": "acompanhamento_veterinario", "records": len(frame), "seed": seed,
                "metrics": {"anomaly_count": int((labels == -1).sum()), "anomaly_fraction": round(float((labels == -1).mean()), 4)},
                "sklearn_version": sklearn.__version__, "evaluation_note": "Fração descritiva de registros marcados; não há rótulo clínico de referência."}
    return {"pipeline": pipeline, "metadata": metadata}
