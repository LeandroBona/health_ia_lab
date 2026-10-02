import pandas as pd

from app.ml.pharmacy.demand.features import FEATURES, next_period_features


def predict_next(bundle: dict, history: pd.DataFrame) -> dict:
    features, period = next_period_features(history)
    estimate = max(0, float(bundle["pipeline"].predict(pd.DataFrame([features])[FEATURES])[0]))
    return {"medication_id": features["medication_id"], "period": period, "prediction": round(estimate), "prediction_raw": round(estimate, 2), "features": features, "algorithm": bundle["metadata"]["algorithm"], "model_version": bundle["metadata"]["version"], "educational_notice": "Estimativa produzida pelo modelo a partir do histórico sintético. Não deve orientar decisões reais de estoque."}
