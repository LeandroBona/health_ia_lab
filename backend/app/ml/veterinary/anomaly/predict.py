import pandas as pd

from .preprocessing import FEATURES


def predict_features(bundle: dict, values: dict) -> dict:
    frame = pd.DataFrame([{key: values.get(key) for key in FEATURES}], columns=FEATURES)
    pipeline = bundle["pipeline"]
    raw = int(pipeline.predict(frame)[0])
    score = float(-pipeline.decision_function(frame)[0])
    return {"classification": "anomalia" if raw == -1 else "padrao", "anomaly_score": round(score, 6),
            "description": "Registro diferente do padrão." if raw == -1 else "Registro semelhante ao padrão aprendido."}
