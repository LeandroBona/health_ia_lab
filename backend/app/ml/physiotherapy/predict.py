import pandas as pd

from app.ml.physiotherapy.feature_config import CLASSES, FEATURES, MODEL_NOTICE
from app.ml.physiotherapy.model_manager import snapshot
from app.ml.physiotherapy.utils import record_fingerprint
from app.schemas.physiotherapy import PatientData, PatientFeatures


def predict(features: PatientFeatures, record: PatientData | None = None) -> dict:
    bundle = snapshot()
    pipeline = bundle["pipeline"]
    frame = pd.DataFrame([features.model_dump(include=set(FEATURES))], columns=FEATURES)
    probabilities = dict(zip(pipeline.classes_, pipeline.predict_proba(frame)[0].tolist()))
    predicted = str(pipeline.predict(frame)[0])
    result = {"prediction": predicted, "probabilities": {label: probabilities[label] for label in CLASSES}, "confidence": max(probabilities.values()), "model_version": bundle["metadata"]["version"], "algorithm": bundle["metadata"]["algorithm"], "educational_notice": MODEL_NOTICE}
    if record is not None:
        member = bundle["membership"].get(record.patient_id)
        partition = member["partition"] if member and member["fingerprint"] == record_fingerprint(record.model_dump()) else "unseen_or_changed"
        result.update({"patient_id": record.patient_id, "actual_result": record.resultado, "correct": predicted == record.resultado, "partition": partition})
    return result
