import pandas as pd

from .feature_config import FEATURES


def predict_features(bundle: dict, values: dict) -> dict:
    frame = pd.DataFrame([{key: values.get(key) for key in FEATURES}], columns=FEATURES)
    pipeline = bundle["pipeline"]
    label = str(pipeline.predict(frame)[0])
    probabilities = {str(label): round(float(value), 6) for label, value in zip(pipeline.classes_, pipeline.predict_proba(frame)[0])}
    return {"animal_id": values.get("animal_id"), "prediction": label, "probabilities": probabilities,
            "actual_result": None, "correct": None}
