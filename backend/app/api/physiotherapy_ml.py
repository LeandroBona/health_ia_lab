from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.ml.physiotherapy import model_manager
from app.ml.physiotherapy.predict import predict
from app.ml.physiotherapy.explain import explain_prediction, get_global_feature_importance
from app.ml.physiotherapy.simulation import FeatureSweepRequest, SimulationRequest, simulate_patient, sweep_feature
from app.models.physiotherapy import PhysiotherapyPatient
from app.schemas.physiotherapy import PatientData, PatientFeatures
from app.services.physiotherapy_validation import DatasetError
from app.services.analysis_history import record as record_history

router = APIRouter(prefix="/fisioterapia", tags=["fisioterapia-model"])


def _patient(db: Session, patient_id: str) -> PatientData:
    patient = db.get(PhysiotherapyPatient, patient_id)
    if patient is None:
        raise DatasetError("Paciente não encontrado.", 404)
    return PatientData.model_validate(patient)


@router.post("/model/train")
def train(db: Session = Depends(get_db)):
    return model_manager.train_model(db)


@router.get("/model")
def model(db: Session = Depends(get_db)):
    return model_manager.model_info(db)


@router.get("/model/evaluation")
def evaluation():
    metadata = model_manager.snapshot()["metadata"]
    return {**metadata["metrics"], "version": metadata["version"], "algorithms": metadata["algorithms"], "selected_model": metadata["selected_model"], "test_samples": metadata["test_samples"], "evaluation_note": metadata["evaluation_note"]}


@router.post("/predict")
def manual_prediction(body: PatientFeatures, db: Session = Depends(get_db)):
    result = predict(body)
    event = record_history(db, module="fisioterapia", analysis_type="physiotherapy_prediction", model_name=result["algorithm"], model_version=result["model_version"], result_summary=f"Categoria: {result['prediction']}; probabilidade: {result['confidence']:.6f}.")
    return result


@router.post("/predict/explain")
def manual_explanation(body: PatientFeatures, db: Session = Depends(get_db)):
    return explain_prediction(body, db)


@router.post("/predict/{patient_id}")
def patient_prediction(patient_id: str, db: Session = Depends(get_db)):
    record = _patient(db, patient_id)
    result = predict(record, record)
    event = record_history(db, module="fisioterapia", analysis_type="physiotherapy_prediction", model_name=result["algorithm"], model_version=result["model_version"], record_reference=patient_id, result_summary=f"Categoria: {result['prediction']}; probabilidade: {result['confidence']:.6f}.")
    return result


@router.get("/model/feature-importance")
def feature_importance(db: Session = Depends(get_db)):
    return get_global_feature_importance(db)


@router.get("/patients/{patient_id}/explanation")
def patient_explanation(patient_id: str, db: Session = Depends(get_db)):
    return explain_prediction(_patient(db, patient_id), db, patient_id)


@router.post("/simulate")
def simulate(body: SimulationRequest, db: Session = Depends(get_db)):
    result = simulate_patient(_patient(db, body.patient_id), body.changes)
    metadata = model_manager.snapshot()["metadata"]
    event = record_history(db, module="fisioterapia", analysis_type="physiotherapy_simulation", model_name=metadata["algorithm"], model_version=metadata["version"], record_reference=body.patient_id, result_summary="Simulação educacional de alteração de variáveis.")
    return result


@router.post("/simulate/feature")
def feature_sweep(body: FeatureSweepRequest, db: Session = Depends(get_db)):
    return sweep_feature(_patient(db, body.patient_id), body.feature, body.values)
