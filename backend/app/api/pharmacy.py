from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database.session import get_db
from app.ml.pharmacy.adherence import model_manager as adherence_model
from app.ml.pharmacy.adherence.predict import predict_features
from app.ml.pharmacy.demand import model_manager as demand_model
from app.ml.pharmacy.demand.predict import predict_next
from app.schemas.pharmacy import ADHERENCE_COLUMNS, DEMAND_COLUMNS, AdherenceFeatures, ConfirmImport
from app.services import pharmacy_dataset as datasets
from app.services import pharmacy_service as service
from app.services.physiotherapy_validation import DatasetError, MAX_BYTES
from app.services.analysis_history import record as record_history

router = APIRouter(prefix="/farmacia", tags=["farmacia"])


@router.get("/{kind}/schema")
def schema(kind: str):
    if kind not in datasets.KINDS:
        raise DatasetError("Tipo de dataset não reconhecido.", 404)
    return {"columns": ADHERENCE_COLUMNS if kind == "adesao" else DEMAND_COLUMNS, "fields": AdherenceFeatures.model_json_schema()["properties"] if kind == "adesao" else {}}


@router.get("/adesao/patients")
def adherence_patients(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = Query(None, max_length=40), categoria: str | None = Query(None, pattern="^(alta|moderada|baixa)$"), db: Session = Depends(get_db)):
    return service.adherence_patients(db, page, page_size, search, categoria)


@router.get("/adesao/patients/{patient_id}")
def adherence_patient(patient_id: str, db: Session = Depends(get_db)):
    return service.adherence_patient(db, patient_id)


@router.get("/adesao/stats")
def adherence_stats(db: Session = Depends(get_db)):
    return service.adherence_stats(db)


@router.get("/adesao/model")
def adherence_info():
    return adherence_model.info()


@router.get("/adesao/model/evaluation")
def adherence_evaluation():
    metadata = adherence_model.snapshot()["metadata"]
    return {**metadata["metrics"], "algorithms": metadata["algorithms"], "selected_model": metadata["algorithm"], "note": metadata["evaluation_note"]}


@router.post("/adesao/model/train")
def train_adherence(db: Session = Depends(get_db)):
    return adherence_model.train_model(db)


@router.post("/adesao/predict/{patient_id}")
def predict_existing(patient_id: str, db: Session = Depends(get_db)):
    patient = service.adherence_patient(db, patient_id)
    result = predict_features(adherence_model.snapshot(), patient)
    event = record_history(db, module="farmacia", analysis_type="pharmacy_adherence", model_name=adherence_model.snapshot()["metadata"]["algorithm"], model_version=result["model_version"], record_reference=patient_id, result_summary=f"Categoria: {result['prediction']}; probabilidade: {result['probabilities'][result['prediction']]}.")
    return {**result, "patient_id": patient_id, "actual_result": patient["categoria_adesao"], "correct": result["prediction"] == patient["categoria_adesao"]}


@router.post("/adesao/predict")
def predict_manual(body: AdherenceFeatures, db: Session = Depends(get_db)):
    result = predict_features(adherence_model.snapshot(), body.model_dump())
    event = record_history(db, module="farmacia", analysis_type="pharmacy_adherence", model_name=adherence_model.snapshot()["metadata"]["algorithm"], model_version=result["model_version"], result_summary=f"Categoria: {result['prediction']}; probabilidade: {result['probabilities'][result['prediction']]}.")
    return result


@router.get("/demanda/medications")
def medications(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = Query(None, max_length=40), db: Session = Depends(get_db)):
    return service.medications(db, page, page_size, search)


@router.get("/demanda/medications/{medication_id}")
def medication(medication_id: str, db: Session = Depends(get_db)):
    return service.medication_detail(db, medication_id)


@router.get("/demanda/stats")
def demand_stats(db: Session = Depends(get_db)):
    return service.demand_stats(db)


@router.get("/demanda/model")
def demand_info():
    metadata = demand_model.info()
    return {key: value for key, value in metadata.items() if key != "test_predictions"}


@router.get("/demanda/model/evaluation")
def demand_evaluation():
    metadata = demand_model.snapshot()["metadata"]
    return {**metadata["metrics"], "algorithms": metadata["algorithms"], "selected_model": metadata["algorithm"], "test_predictions": metadata["test_predictions"], "train_last_period": metadata["train_last_period"], "test_first_period": metadata["test_first_period"], "note": metadata["evaluation_note"]}


@router.post("/demanda/model/train")
def train_demand(db: Session = Depends(get_db)):
    metadata = demand_model.train_model(db)
    return {key: value for key, value in metadata.items() if key != "test_predictions"}


@router.post("/demanda/predict/{medication_id}")
def predict_demand(medication_id: str, db: Session = Depends(get_db)):
    history = service.medication_history(db, medication_id)
    try:
        result = predict_next(demand_model.snapshot(), pd.DataFrame(history))
        event = record_history(db, module="farmacia", analysis_type="pharmacy_demand", model_name=result["algorithm"], model_version=result["model_version"], record_reference=medication_id, result_summary=f"Demanda estimada: {result['prediction']} unidades para {result['period']}.")
        return result
    except ValueError as exc:
        raise DatasetError(str(exc)) from None


@router.get("/{kind}/dataset/download/{format_}")
def download(kind: str, format_: str):
    path = datasets.default_file(kind, format_)
    if not path.is_file():
        raise DatasetError("Arquivo padrão indisponível.", 404)
    return FileResponse(path, filename=path.name, media_type="text/csv" if format_ == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/{kind}/upload")
@router.post("/{kind}/upload/preview")
async def upload(kind: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if kind not in datasets.KINDS:
        raise DatasetError("Tipo de dataset não reconhecido.", 404)
    try:
        content = await file.read(MAX_BYTES + 1)
        filename = Path((file.filename or "arquivo").replace("\\", "/")).name[:255]
        return await run_in_threadpool(datasets.create_preview, db, kind, content, filename)
    finally:
        await file.close()


@router.post("/{kind}/upload/confirm")
def confirm(kind: str, body: ConfirmImport, db: Session = Depends(get_db)):
    if kind not in datasets.KINDS:
        raise DatasetError("Tipo de dataset não reconhecido.", 404)
    return datasets.confirm_import(db, kind, body.token)
