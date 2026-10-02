import pandas as pd

from app.schemas.nursing import FEATURES


def predict_many(pipeline, frame: pd.DataFrame) -> list[dict]:
    if frame.empty:
        return []
    features = frame[FEATURES]
    classifications = pipeline.predict(features)
    scores = pipeline.decision_function(features)
    return [
        {
            "classification": "anomalia" if result == -1 else "padrao",
            "score": round(float(score), 6),
            "anomaly_index": round(float(-score), 6),
        }
        for result, score in zip(classifications, scores)
    ]


def predict_one(pipeline, signals: dict) -> dict:
    return predict_many(pipeline, pd.DataFrame([signals], columns=FEATURES))[0]
