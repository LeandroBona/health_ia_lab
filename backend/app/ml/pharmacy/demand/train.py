import time
from datetime import datetime, timezone

import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.ml.pharmacy.demand.evaluate import evaluate_model
from app.ml.pharmacy.demand.features import FEATURES, add_temporal_features
from app.services.physiotherapy_validation import DatasetError


def chronological_split(featured):
    # Em séries temporais, informações futuras não devem ser utilizadas para prever o passado.
    periods = sorted(featured["period"].unique())
    if len(periods) < 8:
        raise DatasetError("São necessários ao menos 14 períodos consecutivos por medicamento para avaliação temporal.")
    cutoff = periods[int(len(periods) * .8)]
    train = featured[featured["period"] < cutoff]
    test = featured[featured["period"] >= cutoff]
    return train, test, cutoff


def train_candidates(frame, version: str) -> dict:
    started = time.perf_counter()
    featured = add_temporal_features(frame)
    train, test, cutoff = chronological_split(featured)
    if len(train) < 30 or len(test) < 5:
        raise DatasetError("Dataset temporal insuficiente para treinar e avaliar o modelo.")
    numeric = [feature for feature in FEATURES if feature != "medication_id"]
    def pipeline(regressor):
        transformer = ColumnTransformer([
            ("medication", OneHotEncoder(handle_unknown="ignore"), ["medication_id"]),
            ("numeric", SimpleImputer(strategy="median"), numeric),
        ])
        return Pipeline([("preprocessing", transformer), ("regressor", regressor)])
    candidates = {
        "LinearRegression": pipeline(LinearRegression()),
        "RandomForestRegressor": pipeline(RandomForestRegressor(n_estimators=150, min_samples_leaf=2, random_state=42, n_jobs=1)),
    }
    evaluations, predictions = {}, {}
    for name, model in candidates.items():
        model.fit(train[FEATURES], train["demand"])
        evaluations[name], predictions[name] = evaluate_model(model, test[FEATURES], test["demand"])
    selected = min(evaluations, key=lambda name: evaluations[name]["mae"])
    test_rows = [{"medication_id": str(row.medication_id), "period": str(row.period), "observed": int(row.demand), "predicted": round(float(pred), 2)} for row, pred in zip(test.itertuples(), predictions[selected])]
    metadata = {
        "name": "Previsão educacional de demanda farmacêutica", "algorithm": selected, "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(), "record_count": len(frame),
        "training_samples": len(train), "test_samples": len(test), "train_last_period": str(train["period"].max()),
        "test_first_period": str(cutoff), "features": FEATURES, "target": "demand",
        "metrics": evaluations[selected], "algorithms": evaluations, "selection_metric": "mae",
        "test_predictions": test_rows, "training_seconds": round(time.perf_counter() - started, 3),
        "sklearn_version": sklearn.__version__, "random_state": 42,
        "evaluation_note": "A divisão é cronológica. Lags e médias móveis usam exclusivamente demanda de períodos anteriores. O conjunto de teste foi usado para selecionar o algoritmo, não é validação externa.",
    }
    return {"pipeline": candidates[selected], "metadata": metadata}
