"""In-memory counterfactual exercises; database records are never mutated."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError

from app.ml.physiotherapy.feature_config import CLASSES, FEATURES
from app.ml.physiotherapy.predict import predict
from app.schemas.physiotherapy import PatientData, PatientFeatures
from app.services.physiotherapy_validation import DatasetError

EditableFeature = Literal[
    "adesao_exercicios", "faltas", "dor_atual", "mobilidade_atual",
    "forca_muscular", "sessoes_realizadas", "indice_funcional_atual",
]
SweepFeature = Literal[
    "adesao_exercicios", "faltas", "dor_atual", "mobilidade_atual",
    "indice_funcional_atual", "sessoes_realizadas",
]


class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patient_id: str = Field(pattern=r"^PAC-[0-9]{4,8}$")
    changes: dict[EditableFeature, StrictInt] = Field(default_factory=dict, max_length=7)


class FeatureSweepRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patient_id: str = Field(pattern=r"^PAC-[0-9]{4,8}$")
    feature: SweepFeature
    values: list[StrictInt] = Field(min_length=2, max_length=31)


def validated_variant(original: PatientData, changes: dict[str, int]) -> PatientFeatures:
    data = original.model_dump(include=set(FEATURES))
    data.update(changes)
    try:
        return PatientFeatures.model_validate(data)
    except ValidationError as exc:
        details = []
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"]) or "sessões"
            details.append(f"{field}: {error['msg']}")
        raise DatasetError("Alteração inválida. " + "; ".join(details), 422) from None


def _classification(prediction: dict) -> dict:
    return {
        "prediction": prediction["prediction"],
        "probabilities": prediction["probabilities"],
        "confidence": prediction["confidence"],
    }


def compare_predictions(original: dict, simulated: dict) -> dict:
    return {
        "class_changed": original["prediction"] != simulated["prediction"],
        "probability_deltas": {
            label: simulated["probabilities"][label] - original["probabilities"][label]
            for label in CLASSES
        },
    }


def simulate_patient(original: PatientData, changes: dict[str, int]) -> dict:
    variant = validated_variant(original, changes)
    before = _classification(predict(original))
    simulated_prediction = predict(variant)
    after = _classification(simulated_prediction)
    return {
        "patient_id": original.patient_id,
        "original": before, "simulated": after,
        "changes": changes,
        "model_version": simulated_prediction["model_version"],
        **compare_predictions(before, after),
    }


def sweep_feature(original: PatientData, feature: SweepFeature, values: list[int]) -> dict:
    before = _classification(predict(original))
    points = []
    for value in values:
        variant = validated_variant(original, {feature: value})
        points.append({"value": value, **_classification(predict(variant))})
    return {
        "patient_id": original.patient_id, "feature": feature,
        "original_value": getattr(original, feature), "original": before,
        "points": points,
    }
