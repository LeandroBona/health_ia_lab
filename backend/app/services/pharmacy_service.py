"""Read-only data projections for Pharmacy pages."""

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.pharmacy.demand import model_manager as demand_model
from app.ml.pharmacy.demand.predict import predict_next
from app.models.pharmacy import PharmacyAdherencePatient, PharmacyDemandRecord
from app.schemas.pharmacy import ADHERENCE_COLUMNS, DEMAND_COLUMNS
from app.services.physiotherapy_validation import DatasetError


def adherence_row(patient: PharmacyAdherencePatient) -> dict:
    return {key: getattr(patient, key) for key in ADHERENCE_COLUMNS}


def demand_row(record: PharmacyDemandRecord) -> dict:
    return {key: getattr(record, key) for key in DEMAND_COLUMNS}


def adherence_patients(db: Session, page: int, page_size: int, search: str | None = None, category: str | None = None) -> dict:
    query = select(PharmacyAdherencePatient)
    if search:
        query = query.where(PharmacyAdherencePatient.patient_id.ilike(f"%{search}%"))
    if category:
        query = query.where(PharmacyAdherencePatient.categoria_adesao == category)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(PharmacyAdherencePatient.patient_id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [adherence_row(item) for item in items], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}


def adherence_patient(db: Session, patient_id: str) -> dict:
    patient = db.get(PharmacyAdherencePatient, patient_id)
    if patient is None:
        raise DatasetError("Registro não encontrado.", 404)
    return adherence_row(patient)


def adherence_stats(db: Session) -> dict:
    items = db.scalars(select(PharmacyAdherencePatient)).all()
    if not items:
        return {"total_records": 0, "average_adherence": 0, "categories": {}, "by_category": []}
    frame = pd.DataFrame([adherence_row(item) for item in items])
    groups = frame.groupby("categoria_adesao")
    return {
        "total_records": len(frame), "average_adherence": round(float(frame["adesao_percentual"].mean()), 1),
        "categories": frame["categoria_adesao"].value_counts().to_dict(),
        "by_category": [{"category": category, "count": len(group), "average_forgets": round(float(group["esquecimentos_30_dias"].mean()), 1), "average_medicines": round(float(group["quantidade_medicamentos"].mean()), 1)} for category, group in groups],
        "adherence_distribution": [{"range": label, "count": int(count)} for label, count in zip(["0–24%", "25–49%", "50–74%", "75–100%"], pd.cut(frame["adesao_percentual"], bins=[-0.1, 24.99, 49.99, 74.99, 100], include_lowest=True).value_counts(sort=False))],
    }


def medication_history(db: Session, medication_id: str) -> list[dict]:
    items = db.scalars(select(PharmacyDemandRecord).where(PharmacyDemandRecord.medication_id == medication_id).order_by(PharmacyDemandRecord.period)).all()
    if not items:
        raise DatasetError("Medicamento fictício não encontrado.", 404)
    return [demand_row(item) for item in items]


def medication_detail(db: Session, medication_id: str) -> dict:
    history = medication_history(db, medication_id)
    forecast = predict_next(demand_model.snapshot(), pd.DataFrame(history))
    test = [row for row in demand_model.snapshot()["metadata"]["test_predictions"] if row["medication_id"] == medication_id]
    return {"medication_id": medication_id, "history": history, "prediction": forecast, "test_predictions": test, "average_demand": round(sum(row["demand"] for row in history) / len(history), 1), "last_demand": history[-1]["demand"]}


def medications(db: Session, page: int, page_size: int, search: str | None = None) -> dict:
    query = select(PharmacyDemandRecord.medication_id).distinct().order_by(PharmacyDemandRecord.medication_id)
    if search:
        query = query.where(PharmacyDemandRecord.medication_id.ilike(f"%{search}%"))
    all_ids = db.scalars(query).all()
    ids = all_ids[(page - 1) * page_size:page * page_size]
    items = []
    for medication_id in ids:
        detail = medication_detail(db, medication_id)
        history = detail["history"]
        first, last = history[0]["demand"], history[-1]["demand"]
        items.append({"medication_id": medication_id, "average_demand": detail["average_demand"], "last_demand": last, "next_prediction": detail["prediction"]["prediction"], "trend": round((last - first) / max(first, 1) * 100, 1), "periods": len(history)})
    return {"items": items, "total": len(all_ids), "page": page, "page_size": page_size, "pages": (len(all_ids) + page_size - 1) // page_size}


def demand_stats(db: Session) -> dict:
    count = db.scalar(select(func.count()).select_from(PharmacyDemandRecord)) or 0
    meds = db.scalar(select(func.count(func.distinct(PharmacyDemandRecord.medication_id)))) or 0
    periods = db.scalar(select(func.count(func.distinct(PharmacyDemandRecord.period)))) or 0
    used = db.scalar(select(func.sum(PharmacyDemandRecord.quantity_used))) or 0
    return {"medications": meds, "periods": periods, "records": count, "total_consumption": int(used)}
