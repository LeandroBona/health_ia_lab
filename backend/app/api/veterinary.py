from pathlib import Path

import pandas as pd

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database.session import get_db
from app.data_generators.veterinary import ANIMAL_COLUMNS
from app.data_generators.veterinary_followup import FOLLOWUP_COLUMNS
from app.ml.veterinary.classification import model_manager as classification_model
from app.ml.veterinary.classification.predict import predict_features as classify
from app.ml.veterinary.anomaly import model_manager as anomaly_model
from app.ml.veterinary.anomaly.predict import predict_features as detect
from app.ml.veterinary.anomaly.preprocessing import FEATURES as ANOMALY_FEATURES
from app.models.veterinary import VeterinaryAnimal, VeterinaryDataset, VeterinaryFollowUp
from app.schemas.veterinary import AnimalFeatures, ConfirmImport, FollowUpFeatures
from app.services import veterinary_dataset as datasets
from app.services.physiotherapy_validation import DatasetError, MAX_BYTES
from app.services.analysis_history import record as record_history

router = APIRouter(prefix="/veterinaria", tags=["veterinaria"])
NOTICE = "Os dados e resultados apresentados neste módulo são sintéticos e possuem finalidade exclusivamente educacional."


def animal_dict(item: VeterinaryAnimal) -> dict:
    return {key: getattr(item, key) for key in ANIMAL_COLUMNS}


def followup_dict(item: VeterinaryFollowUp) -> dict:
    return {**{key: getattr(item, key) for key in FOLLOWUP_COLUMNS}, "classification": item.classification, "anomaly_score": item.anomaly_score}


@router.get("/animals")
def animals(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), animal_id: str | None = None,
            especie: str | None = None, sexo: str | None = None, procedimento: str | None = None, evolucao: str | None = None,
            db: Session = Depends(get_db)):
    query = select(VeterinaryAnimal)
    for column, value in ((VeterinaryAnimal.especie, especie), (VeterinaryAnimal.sexo, sexo), (VeterinaryAnimal.procedimento, procedimento), (VeterinaryAnimal.evolucao, evolucao)):
        if value:
            query = query.where(column == value)
    if animal_id:
        query = query.where(VeterinaryAnimal.animal_id.contains(animal_id))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(VeterinaryAnimal.animal_id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [animal_dict(item) for item in items], "total": total, "page": page, "page_size": page_size}


@router.get("/animals/{animal_id}")
def animal(animal_id: str, db: Session = Depends(get_db)):
    item = db.get(VeterinaryAnimal, animal_id)
    if item is None:
        raise DatasetError("Animal fictício não encontrado.", 404)
    followups = db.scalars(select(VeterinaryFollowUp).where(VeterinaryFollowUp.animal_id == animal_id).order_by(VeterinaryFollowUp.timestamp)).all()
    return {**animal_dict(item), "followups": [followup_dict(record) for record in followups]}


@router.get("/animals/{animal_id}/anomalies")
def animal_anomalies(animal_id: str, db: Session = Depends(get_db)):
    if db.get(VeterinaryAnimal, animal_id) is None:
        raise DatasetError("Animal fictício não encontrado.", 404)
    records = db.scalars(select(VeterinaryFollowUp).where(VeterinaryFollowUp.animal_id == animal_id).order_by(VeterinaryFollowUp.timestamp)).all()
    return {"animal_id": animal_id, "items": [followup_dict(record) for record in records], "anomalies": sum(item.classification == "anomalia" for item in records)}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    def counts(column):
        return {str(value): count for value, count in db.execute(select(column, func.count()).group_by(column)).all()}
    return {"animals": db.scalar(select(func.count()).select_from(VeterinaryAnimal)) or 0,
            "followups": db.scalar(select(func.count()).select_from(VeterinaryFollowUp)) or 0,
            "analyzed": db.scalar(select(func.count()).select_from(VeterinaryFollowUp).where(VeterinaryFollowUp.classification.is_not(None))) or 0,
            "anomalies": db.scalar(select(func.count()).select_from(VeterinaryFollowUp).where(VeterinaryFollowUp.classification == "anomalia")) or 0,
            "species": counts(VeterinaryAnimal.especie), "procedures": counts(VeterinaryAnimal.procedimento), "evolution": counts(VeterinaryAnimal.evolucao),
            "averages": {key: round(float(db.scalar(select(func.avg(getattr(VeterinaryAnimal, key)))) or 0), 1) for key in ("atividade_percentual", "alimentacao_percentual", "indice_recuperacao")},
            "notice": NOTICE}


@router.get("/model")
def model():
    return classification_model.info()


@router.get("/model/evaluation")
def evaluation():
    info = classification_model.info()
    return {"metrics": info["metrics"], "algorithms": info["algorithms"], "selected_model": info["algorithm"], "note": info["evaluation_note"]}


@router.post("/model/train")
def train(db: Session = Depends(get_db)):
    return classification_model.train_model(db)


@router.post("/predict/{animal_id}")
def predict_animal(animal_id: str, db: Session = Depends(get_db)):
    item = db.get(VeterinaryAnimal, animal_id)
    if item is None:
        raise DatasetError("Animal fictício não encontrado.", 404)
    result = classify(classification_model.snapshot(), animal_dict(item))
    metadata = classification_model.snapshot()["metadata"]
    event = record_history(db, module="veterinaria", analysis_type="veterinary_prediction", model_name=metadata["algorithm"], model_version=metadata["version"], record_reference=animal_id, result_summary=f"Categoria: {result['prediction']}; probabilidade: {result['probabilities'][result['prediction']]}.")
    return {**result, "actual_result": item.evolucao, "correct": result["prediction"] == item.evolucao}


@router.post("/predict")
def predict_manual(body: AnimalFeatures, db: Session = Depends(get_db)):
    result = classify(classification_model.snapshot(), body.model_dump())
    metadata = classification_model.snapshot()["metadata"]
    event = record_history(db, module="veterinaria", analysis_type="veterinary_prediction", model_name=metadata["algorithm"], model_version=metadata["version"], result_summary=f"Categoria: {result['prediction']}; probabilidade: {result['probabilities'][result['prediction']]}.")
    return result


@router.get("/anomalies/model")
def anomaly_info():
    return anomaly_model.info()


@router.post("/anomalies/model/train")
def train_anomaly(db: Session = Depends(get_db)):
    return anomaly_model.train_model(db)


@router.post("/anomalies/analyze")
def analyze(db: Session = Depends(get_db)):
    records = db.scalars(select(VeterinaryFollowUp)).all()
    bundle = anomaly_model.snapshot()
    frame = pd.DataFrame([{feature: getattr(record, feature) for feature in ANOMALY_FEATURES} for record in records], columns=ANOMALY_FEATURES)
    if not frame.empty:
        pipeline = bundle["pipeline"]
        labels = pipeline.predict(frame)
        scores = -pipeline.decision_function(frame)
        for record, label, score in zip(records, labels, scores):
            record.classification = "anomalia" if label == -1 else "padrao"
            record.anomaly_score = round(float(score), 6)
    db.commit()
    anomalies = sum(record.classification == "anomalia" for record in records)
    metadata = bundle["metadata"]
    event = record_history(db, module="veterinaria", analysis_type="veterinary_anomaly", model_name="Isolation Forest", model_version=metadata["version"], result_summary=f"Análise temporal: {len(records)} acompanhamentos; {anomalies} diferentes do padrão.")
    return {"success": True, "total": len(records), "anomalies": anomalies}


@router.post("/anomalies/predict")
def predict_anomaly(body: FollowUpFeatures, db: Session = Depends(get_db)):
    result = detect(anomaly_model.snapshot(), body.model_dump())
    event = record_history(db, module="veterinaria", analysis_type="veterinary_anomaly", model_name="Isolation Forest", model_version=anomaly_model.snapshot()["metadata"]["version"], result_summary=f"Categoria: {result['classification']}; índice: {result['anomaly_score']}.")
    return result


@router.get("/{kind}/schema")
def schema(kind: str):
    if kind not in datasets.CONFIG:
        raise DatasetError("Tipo de dataset não reconhecido.", 404)
    return {"columns": datasets.DATASET_COLUMNS[kind]}


@router.get("/{kind}/dataset/download/{format_}")
def download(kind: str, format_: str):
    path = datasets.default_file(kind, format_)
    if not path.is_file():
        raise DatasetError("Arquivo padrão indisponível.", 404)
    return FileResponse(path, filename=path.name)


@router.post("/{kind}/upload/preview")
async def upload(kind: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read(MAX_BYTES + 1)
        filename = Path((file.filename or "arquivo").replace("\\", "/")).name[:255]
        return await run_in_threadpool(datasets.create_preview, db, kind, content, filename)
    finally:
        await file.close()


@router.post("/{kind}/upload/confirm")
def confirm(kind: str, body: ConfirmImport, db: Session = Depends(get_db)):
    return datasets.confirm_import(db, kind, body.token)
