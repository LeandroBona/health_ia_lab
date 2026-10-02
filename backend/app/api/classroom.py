"""Lightweight classroom preparation and synthetic demonstration references."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.physiotherapy import PhysiotherapyPatient
from app.models.nursing import NursingMeasurement
from app.models.pharmacy import PharmacyAdherencePatient, PharmacyDemandRecord
from app.models.veterinary import VeterinaryAnimal
from app.models.psychology import PsychologyRecord
from app.schemas.physiotherapy import PatientData
from app.ml.physiotherapy.predict import predict as predict_physiotherapy
from app.services.llm.llm_service import LLMService
from app.services.platform_catalog import datasets, models

router = APIRouter(prefix="/classroom", tags=["modo-aula"])


@router.get("/readiness")
def readiness(db: Session = Depends(get_db)):
    """Read metadata only; opening the preparation screen never runs a model."""
    try:
        db.execute(select(func.count()).select_from(PhysiotherapyPatient))
        database = True
        dataset_items = datasets(db)
    except Exception:
        database = False
        dataset_items = []
    model_items = {item["id"]: item["status"] == "ready" for item in models()}
    llm = LLMService().status()
    return {
        "backend": True,
        "database": database,
        "physiotherapy_model": model_items.get("physiotherapy-classification", False),
        "nursing_model": model_items.get("nursing-anomaly", False),
        "pharmacy_models": model_items.get("pharmacy-adherence", False) and model_items.get("pharmacy-demand", False),
        "veterinary_models": model_items.get("veterinary-classification", False) and model_items.get("veterinary-anomaly", False),
        "psychology_model": model_items.get("psychology-classification", False),
        "datasets": sum(item["records"] > 0 for item in dataset_items),
        "llm": {"available": llm["available"], "mode": llm["mode"], "provider": llm["provider"]},
        "vision": "browser",
    }


def first_value(db: Session, column):
    return db.scalar(select(column).order_by(column).limit(1))


@router.get("/scenarios")
def scenarios(db: Session = Depends(get_db)):
    """Choose existing fictitious records, without embedding fixed IDs in the UI."""
    candidates = db.scalars(select(PhysiotherapyPatient).order_by(PhysiotherapyPatient.patient_id).limit(30)).all()
    selected = candidates[0] if candidates else None
    if candidates:
        # Prefer a non-extreme class distribution for classroom discussion.
        try:
            selected = min(candidates, key=lambda row: abs(max(predict_physiotherapy(PatientData.model_validate(row))["probabilities"].values()) - 0.65))
        except (RuntimeError, ValueError, KeyError):
            selected = candidates[0]
    nursing_pattern = db.scalar(select(NursingMeasurement.measurement_id).where(NursingMeasurement.classification == "padrao").limit(1))
    nursing_anomaly = db.scalar(select(NursingMeasurement.measurement_id).where(NursingMeasurement.classification == "anomalia").limit(1))
    return {
        "physiotherapy_patient_id": selected.patient_id if selected else None,
        "nursing_pattern_id": nursing_pattern or first_value(db, NursingMeasurement.measurement_id),
        "nursing_anomaly_id": nursing_anomaly,
        "pharmacy_patient_id": first_value(db, PharmacyAdherencePatient.patient_id),
        "pharmacy_medication_id": first_value(db, PharmacyDemandRecord.medication_id),
        "veterinary_animal_id": first_value(db, VeterinaryAnimal.animal_id),
        "psychology_record_id": first_value(db, PsychologyRecord.record_id),
    }
