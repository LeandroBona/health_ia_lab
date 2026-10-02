from app.schemas.dashboard import DashboardResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.physiotherapy import PhysiotherapyPatient, PhysiotherapyDataset
from app.ml.physiotherapy.model_manager import available_count
from app.models.nursing import NursingPatient, NursingMeasurement, NursingDataset
from app.ml.nursing.anomaly_service import model_info as nursing_model_info
from app.models.pharmacy import PharmacyAdherencePatient, PharmacyDataset
from app.ml.pharmacy.adherence import model_manager as adherence_model
from app.ml.pharmacy.demand import model_manager as demand_model
from app.models.veterinary import VeterinaryAnimal, VeterinaryDataset, VeterinaryFollowUp
from app.ml.veterinary.classification import model_manager as veterinary_model
from app.ml.veterinary.anomaly import model_manager as veterinary_anomaly_model
from app.models.psychology import PsychologyRecord, PsychologyDataset
from app.ml.psychology import model_manager as psychology_model


def get_dashboard_summary(db: Session) -> DashboardResponse:
    """Counts represent stored synthetic records, not clinical analyses."""
    return DashboardResponse(
        patients=(db.scalar(select(func.count()).select_from(PhysiotherapyPatient)) or 0) + (db.scalar(select(func.count()).select_from(NursingPatient)) or 0) + (db.scalar(select(func.count()).select_from(PharmacyAdherencePatient)) or 0) + (db.scalar(select(func.count()).select_from(VeterinaryAnimal)) or 0) + (db.scalar(select(func.count()).select_from(PsychologyRecord)) or 0),
        datasets=(db.scalar(select(func.count()).select_from(PhysiotherapyDataset)) or 0) + (db.scalar(select(func.count()).select_from(NursingDataset)) or 0) + (db.scalar(select(func.count()).select_from(PharmacyDataset)) or 0) + (db.scalar(select(func.count()).select_from(VeterinaryDataset)) or 0) + (db.scalar(select(func.count()).select_from(PsychologyDataset)) or 0),
        analyses=(db.scalar(select(func.count()).select_from(NursingMeasurement).where(NursingMeasurement.classification.is_not(None))) or 0) + (db.scalar(select(func.count()).select_from(VeterinaryFollowUp).where(VeterinaryFollowUp.classification.is_not(None))) or 0) + (db.scalar(select(func.count()).select_from(PsychologyRecord)) or 0),
        models=available_count() + int(nursing_model_info()["status"] == "ready") + int(adherence_model._bundle is not None) + int(demand_model._bundle is not None) + int(veterinary_model._bundle is not None) + int(veterinary_anomaly_model._bundle is not None) + 3 * int(psychology_model._bundle is not None),
        anomalies=(db.scalar(select(func.count()).select_from(NursingMeasurement).where(NursingMeasurement.classification == "anomalia")) or 0) + (db.scalar(select(func.count()).select_from(VeterinaryFollowUp).where(VeterinaryFollowUp.classification == "anomalia")) or 0),
    )
