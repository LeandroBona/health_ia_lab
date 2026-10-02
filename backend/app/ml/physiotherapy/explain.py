"""SHAP explanations for the saved preprocessing + classifier pipeline.

SHAP is computed only on request. Encoded columns are summed back into their
original variables before anything is shown to students.
"""

import threading

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.ml.physiotherapy.feature_config import (
    CATEGORICAL_FEATURES, CLASSES, EXPLANATION_NOTICE, FEATURE_LABELS,
    FEATURES, NUMERIC_FEATURES,
)
from app.ml.physiotherapy.model_manager import snapshot, training_frame
from app.ml.physiotherapy.predict import predict
from app.schemas.physiotherapy import PatientFeatures
from app.services.physiotherapy_validation import DatasetError

_cache_lock = threading.RLock()
_cached_bundle: dict | None = None
_cached_explainer = None
_cached_global: dict | None = None


def transformed_feature_names(pipeline) -> tuple[list[str], list[str]]:
    """Return sklearn output names and the corresponding source field per column."""
    preprocessor = pipeline.named_steps["preprocessing"]
    names = list(preprocessor.get_feature_names_out())
    encoder = preprocessor.named_transformers_["categorical"].named_steps["encoder"]
    source = list(NUMERIC_FEATURES)
    for field, categories in zip(CATEGORICAL_FEATURES, encoder.categories_, strict=True):
        source.extend([field] * len(categories))
    if len(names) != len(source):
        raise DatasetError("As colunas transformadas do modelo não correspondem às variáveis originais.", 409)
    return names, source


def _sample_frames(bundle: dict, db: Session) -> tuple[pd.DataFrame, pd.DataFrame]:
    if "explanation_background" in bundle and "explanation_test_sample" in bundle:
        return (
            pd.DataFrame(bundle["explanation_background"], columns=FEATURES),
            pd.DataFrame(bundle["explanation_test_sample"], columns=FEATURES),
        )
    # Compatibility with the model artifact saved before this stage.
    frame = training_frame(db, bundle["metadata"]["dataset_source"])
    members = bundle["membership"]
    train = frame[frame.patient_id.map(lambda key: members.get(key, {}).get("partition") == "train")]
    test = frame[frame.patient_id.map(lambda key: members.get(key, {}).get("partition") == "test")]
    if train.empty or test.empty:
        raise DatasetError("A amostra do modelo anterior não está disponível. Treine o modelo novamente.", 409)
    return train[FEATURES].head(40), test[FEATURES].head(60)


def _explainer(bundle: dict, db: Session):
    global _cached_bundle, _cached_explainer, _cached_global
    with _cache_lock:
        if _cached_bundle is bundle and _cached_explainer is not None:
            return _cached_explainer
        import shap

        pipeline = bundle["pipeline"]
        classifier = pipeline.named_steps["classifier"]
        if bundle["metadata"]["algorithm"] == "RandomForestClassifier":
            explainer = shap.TreeExplainer(classifier)
        elif bundle["metadata"]["algorithm"] == "LogisticRegression":
            background, _ = _sample_frames(bundle, db)
            transformed = pipeline.named_steps["preprocessing"].transform(background)
            explainer = shap.LinearExplainer(classifier, np.asarray(transformed, dtype=float))
        else:
            raise DatasetError("O algoritmo salvo não possui explicador nesta versão.", 409)
        _cached_bundle, _cached_explainer, _cached_global = bundle, explainer, None
        return explainer


def _values(bundle: dict, db: Session, frame: pd.DataFrame) -> np.ndarray:
    pipeline = bundle["pipeline"]
    transformed = np.asarray(pipeline.named_steps["preprocessing"].transform(frame[FEATURES]), dtype=float)
    raw = _explainer(bundle, db).shap_values(transformed)
    if isinstance(raw, list):
        values = np.stack(raw, axis=-1)
    else:
        values = np.asarray(raw)
    if values.ndim == 2 and len(CLASSES) == 2:
        values = np.stack([-values, values], axis=-1)
    if values.shape != (len(frame), transformed.shape[1], len(CLASSES)):
        raise DatasetError("O formato da explicação do modelo é incompatível com suas classes.", 409)
    if not np.isfinite(values).all():
        raise DatasetError("A explicação retornou valores não finitos.", 409)
    return values


def _grouped(bundle: dict, values: np.ndarray) -> np.ndarray:
    _, sources = transformed_feature_names(bundle["pipeline"])
    grouped = np.zeros((values.shape[0], len(FEATURES), len(CLASSES)), dtype=float)
    for output_index, source in enumerate(sources):
        grouped[:, FEATURES.index(source), :] += values[:, output_index, :]
    return grouped


def _impact_level(magnitude: float, maximum: float) -> str:
    relative = magnitude / maximum if maximum else 0
    if relative < .2:
        return "Muito baixo"
    if relative < .4:
        return "Baixo"
    if relative < .6:
        return "Moderado"
    if relative < .8:
        return "Alto"
    return "Muito alto"


def get_local_feature_importance(features: PatientFeatures, db: Session) -> dict:
    bundle = snapshot()
    frame = pd.DataFrame([features.model_dump(include=set(FEATURES))], columns=FEATURES)
    prediction = predict(features)
    class_index = list(bundle["pipeline"].classes_).index(prediction["prediction"])
    impacts = _grouped(bundle, _values(bundle, db, frame))[0, :, class_index]
    maximum = max(np.abs(impacts), default=0)
    factors = [
        {
            "feature": field, "label": FEATURE_LABELS[field],
            "value": getattr(features, field), "impact": float(impact),
            "intensity": _impact_level(abs(float(impact)), float(maximum)),
        }
        for field, impact in zip(FEATURES, impacts, strict=True)
    ]
    factors.sort(key=lambda factor: abs(factor["impact"]), reverse=True)
    return {
        **prediction, "probability": prediction["probabilities"][prediction["prediction"]],
        "impact_unit": "probability_points" if bundle["metadata"]["algorithm"] == "RandomForestClassifier" else "logit_units",
        "positive_factors": [factor for factor in factors if factor["impact"] > 1e-10],
        "negative_factors": [factor for factor in factors if factor["impact"] < -1e-10],
        "factors": factors, "explanation_notice": EXPLANATION_NOTICE,
    }


def explain_prediction(features: PatientFeatures, db: Session, patient_id: str | None = None) -> dict:
    explanation = get_local_feature_importance(features, db)
    if patient_id:
        explanation["patient_id"] = patient_id
    return explanation


def get_global_feature_importance(db: Session) -> dict:
    global _cached_global
    bundle = snapshot()
    with _cache_lock:
        if _cached_bundle is bundle and _cached_global is not None:
            return _cached_global
    _, test = _sample_frames(bundle, db)
    values = _grouped(bundle, _values(bundle, db, test))
    magnitudes = np.abs(values).mean(axis=(0, 2))
    total = float(magnitudes.sum())
    ranked = sorted(
        (
            {"feature": field, "label": FEATURE_LABELS[field],
             "importance": float(magnitude / total) if total else 0.0}
            for field, magnitude in zip(FEATURES, magnitudes, strict=True)
        ),
        key=lambda item: item["importance"], reverse=True,
    )
    result = {
        "features": ranked, "sample_size": len(test), "sample_source": "test",
        "model_version": bundle["metadata"]["version"], "method": "mean_absolute_shap",
        "explanation_notice": EXPLANATION_NOTICE,
    }
    with _cache_lock:
        if _cached_bundle is bundle:
            _cached_global = result
    return result
