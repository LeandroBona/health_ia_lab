import pandas as pd

from app.ml.pharmacy.adherence.feature_config import CLASSES, FEATURES, NOTICE


def predict_features(bundle: dict, features: dict) -> dict:
    pipeline = bundle["pipeline"]
    x = pd.DataFrame([{key: features[key] for key in FEATURES}])
    probabilities = pipeline.predict_proba(x)[0]
    labels = pipeline.classes_
    values = {label: round(float(probabilities[list(labels).index(label)]), 6) for label in CLASSES}
    predicted = str(pipeline.predict(x)[0])
    return {"prediction": predicted, "probabilities": values, "model_version": bundle["metadata"]["version"], "educational_notice": NOTICE}
