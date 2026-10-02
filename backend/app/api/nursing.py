from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database.session import get_db
from app.ml.nursing import anomaly_service as model
from app.schemas.nursing import ConfirmImport, FEATURES, REQUIRED_COLUMNS, Signals
from app.services import nursing_dataset as datasets
from app.services import nursing_service as service
from app.services.physiotherapy_validation import DatasetError, MAX_BYTES
from app.services.analysis_history import record as record_history

router = APIRouter(prefix="/enfermagem", tags=["enfermagem"])


@router.get("/schema")
def schema():
    return {"columns": REQUIRED_COLUMNS, "features": FEATURES, "fields": Signals.model_json_schema()["properties"]}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return service.stats(db)


@router.get("/patients")
def patients(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = Query(None, max_length=40), db: Session = Depends(get_db)):
    return service.list_patients(db, page, page_size, search)


@router.get("/patients/{patient_id}")
def patient(patient_id: str, db: Session = Depends(get_db)):
    return service.patient_detail(db, patient_id)


@router.get("/patients/{patient_id}/measurements")
def patient_measurements(patient_id: str, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    service.patient_detail(db, patient_id)
    return service.list_measurements(db, page, page_size, patient_id=patient_id, sort="time")


@router.get("/measurements")
def measurements(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), patient_id: str | None = None, classification: str | None = Query("anomalia", pattern="^(anomalia|padrao|all)$"), date_from: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"), date_to: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"), db: Session = Depends(get_db)):
    return service.list_measurements(db, page, page_size, patient_id, None if classification == "all" else classification, date_from, date_to)


@router.get("/measurements/{measurement_id}")
def measurement(measurement_id: str, db: Session = Depends(get_db)):
    return service.measurement_detail(db, measurement_id)


@router.get("/model")
def model_details(db: Session = Depends(get_db)):
    return {**model.model_info(), "current_anomalies": service.stats(db)["anomalies"]}


@router.get("/model/evaluation")
def evaluation():
    return model.snapshot()["metadata"]["evaluation"]


@router.post("/model/train")
def train(db: Session = Depends(get_db)):
    return {**model.train_model(db), "status": "ready", "current_anomalies": service.stats(db)["anomalies"]}


@router.post("/anomalies/analyze")
def analyze(db: Session = Depends(get_db)):
    result = model.analyze_all(db)
    event = record_history(db, module="enfermagem", analysis_type="nursing_anomaly", model_name="Isolation Forest", model_version=result["model_version"], result_summary=f"Análise temporal: {result['total']} medições; {result['anomalies']} registros diferentes do padrão.")
    return result


@router.post("/anomalies/predict")
def predict(body: Signals, db: Session = Depends(get_db)):
    result = model.predict_signals(body.model_dump())
    event = record_history(db, module="enfermagem", analysis_type="nursing_anomaly", model_name="Isolation Forest", model_version=result["model_version"], result_summary=f"Categoria: {result['classification']}; índice: {result['anomaly_index']}.")
    return result


@router.get("/dataset")
def dataset(db: Session = Depends(get_db)):
    return datasets.dataset_info(db)


@router.get("/dataset/explore")
def explore(column: str = "frequencia_cardiaca", db: Session = Depends(get_db)):
    return service.explore(db, column)


@router.get("/dataset/timeline")
def timeline(db: Session = Depends(get_db)):
    return service.timeline(db)


@router.get("/dataset/download/{format}")
def download(format: str):
    if format not in {"csv", "xlsx"}:
        raise DatasetError("Formato não suportado.", 404)
    filename = f"monitoramento_enfermagem.{format}"
    path = datasets.DATASET_DIR / filename
    if not path.is_file():
        raise DatasetError("Arquivo padrão indisponível.", 404)
    return FileResponse(path, filename=filename, media_type="text/csv" if format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/upload")
@router.post("/upload/preview")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read(MAX_BYTES + 1)
        filename = Path((file.filename or "arquivo").replace("\\", "/")).name[:255]
        return await run_in_threadpool(datasets.create_preview, db, content, filename)
    finally:
        await file.close()


@router.post("/upload/confirm")
def confirm(body: ConfirmImport, db: Session = Depends(get_db)):
    result = datasets.confirm_import(db, body.token)
    if result["imported"]:
        # Existing model is applied to the newly imported measurements; training remains explicit.
        model.analyze_all(db)
    return result
