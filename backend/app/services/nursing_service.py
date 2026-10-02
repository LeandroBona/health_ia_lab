"""Read-only queries and statistical summaries for the nursing UI."""

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.nursing import NursingAnalysisRun, NursingMeasurement, NursingPatient
from app.schemas.nursing import FEATURES
from app.services.physiotherapy_validation import DatasetError


def _page(query, count_query, db: Session, page: int, page_size: int) -> dict:
    total = db.scalar(count_query) or 0
    return {"items": [row for row in db.scalars(query.offset((page - 1) * page_size).limit(page_size))], "page": page, "page_size": page_size, "total": total, "pages": max(1, (total + page_size - 1) // page_size)}


def list_patients(db: Session, page: int, page_size: int, search: str | None) -> dict:
    counts = select(NursingMeasurement.patient_id, func.count().label("measurements"), func.sum(func.iif(NursingMeasurement.classification == "anomalia", 1, 0)).label("anomalies")).group_by(NursingMeasurement.patient_id).subquery()
    query = select(NursingPatient.patient_id, NursingPatient.idade, counts.c.measurements, counts.c.anomalies).outerjoin(counts, counts.c.patient_id == NursingPatient.patient_id)
    total_query = select(func.count()).select_from(NursingPatient)
    if search:
        condition = NursingPatient.patient_id.ilike(f"%{search.strip()}%")
        query = query.where(condition)
        total_query = total_query.where(condition)
    total = db.scalar(total_query) or 0
    rows = db.execute(query.order_by(NursingPatient.patient_id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [{"patient_id": row.patient_id, "idade": row.idade, "measurements": row.measurements or 0, "anomalies": row.anomalies or 0} for row in rows], "page": page, "page_size": page_size, "total": total, "pages": max(1, (total + page_size - 1) // page_size)}


def patient_detail(db: Session, patient_id: str) -> dict:
    patient = db.get(NursingPatient, patient_id)
    if patient is None:
        raise DatasetError("Paciente sintético não encontrado.", 404)
    count = db.scalar(select(func.count()).select_from(NursingMeasurement).where(NursingMeasurement.patient_id == patient_id)) or 0
    anomalies = db.scalar(select(func.count()).select_from(NursingMeasurement).where(NursingMeasurement.patient_id == patient_id, NursingMeasurement.classification == "anomalia")) or 0
    means = db.execute(select(*(func.avg(getattr(NursingMeasurement, feature)) for feature in FEATURES)).where(NursingMeasurement.patient_id == patient_id)).one()
    return {"patient_id": patient_id, "idade": patient.idade, "measurements": count, "anomalies": anomalies, "anomaly_percentage": round(100 * anomalies / count, 1) if count else 0, "averages": {feature: round(float(value or 0), 2) for feature, value in zip(FEATURES, means)}}


def list_measurements(db: Session, page: int, page_size: int, patient_id: str | None = None, classification: str | None = None, date_from: str | None = None, date_to: str | None = None, sort: str = "anomaly") -> dict:
    query = select(NursingMeasurement)
    count_query = select(func.count()).select_from(NursingMeasurement)
    conditions = []
    if patient_id:
        conditions.append(NursingMeasurement.patient_id == patient_id)
    if classification:
        conditions.append(NursingMeasurement.classification == classification)
    if date_from:
        conditions.append(NursingMeasurement.timestamp >= date_from)
    if date_to:
        conditions.append(NursingMeasurement.timestamp <= date_to + "T23:59:59+00:00")
    if conditions:
        query = query.where(*conditions)
        count_query = count_query.where(*conditions)
    order = [asc(NursingMeasurement.anomaly_score), asc(NursingMeasurement.measurement_id)] if sort == "anomaly" else [asc(NursingMeasurement.timestamp), asc(NursingMeasurement.measurement_id)]
    query = query.order_by(*order)
    page_data = _page(query, count_query, db, page, page_size)
    page_data["items"] = [measurement_dict(item) for item in page_data["items"]]
    return page_data


def measurement_dict(item: NursingMeasurement) -> dict:
    return {"measurement_id": item.measurement_id, "patient_id": item.patient_id, "timestamp": item.timestamp, "idade": item.idade, **{feature: getattr(item, feature) for feature in FEATURES}, "estado": item.estado, "classification": item.classification, "score": item.anomaly_score, "anomaly_index": round(-item.anomaly_score, 6) if item.anomaly_score is not None else None}


def measurement_detail(db: Session, measurement_id: str) -> dict:
    item = db.get(NursingMeasurement, measurement_id)
    if item is None:
        raise DatasetError("Medição não encontrada.", 404)
    patient_means = db.execute(select(*(func.avg(getattr(NursingMeasurement, feature)) for feature in FEATURES)).where(NursingMeasurement.patient_id == item.patient_id)).one()
    general_means = db.execute(select(*(func.avg(getattr(NursingMeasurement, feature)) for feature in FEATURES))).one()
    comparisons = {}
    for feature, patient_average, general_average in zip(FEATURES, patient_means, general_means):
        value = getattr(item, feature)
        comparisons[feature] = {"value": value, "patient_average": round(float(patient_average), 2), "dataset_average": round(float(general_average), 2), "patient_difference": round(value - patient_average, 2), "dataset_difference": round(value - general_average, 2)}
    return {**measurement_dict(item), "comparisons": comparisons}


def stats(db: Session) -> dict:
    patients = db.scalar(select(func.count()).select_from(NursingPatient)) or 0
    measurements = db.scalar(select(func.count()).select_from(NursingMeasurement)) or 0
    anomalies = db.scalar(select(func.count()).select_from(NursingMeasurement).where(NursingMeasurement.classification == "anomalia")) or 0
    run = db.get(NursingAnalysisRun, "latest")
    return {"total_patients": patients, "total_measurements": measurements, "average_measurements_per_patient": round(measurements / patients, 1) if patients else 0, "anomalies": anomalies, "anomaly_percentage": round(100 * anomalies / measurements, 1) if measurements else 0, "last_analysis": run.analyzed_at if run else None}


def timeline(db: Session) -> list[dict]:
    date = func.substr(NursingMeasurement.timestamp, 1, 10)
    rows = db.execute(select(date.label("date"), func.count().label("measurements"), func.sum(func.iif(NursingMeasurement.classification == "anomalia", 1, 0)).label("anomalies")).group_by(date).order_by(date)).all()
    return [{"date": row.date, "measurements": row.measurements, "anomalies": row.anomalies or 0} for row in rows]


def explore(db: Session, column: str) -> dict:
    if column not in ["idade", *FEATURES, "estado", "classification"]:
        raise DatasetError("Coluna não disponível para exploração.")
    values = db.scalars(select(getattr(NursingMeasurement, column))).all()
    if column in {"estado", "classification"}:
        distribution = {str(value): values.count(value) for value in sorted(set(values), key=str)}
        return {"column": column, "type": "categorical", "count": len(values), "missing": values.count(None), "distribution": distribution}
    import pandas as pd
    series = pd.Series(values, dtype=float)
    return {"column": column, "type": "numeric", "count": len(values), "missing": int(series.isna().sum()), "mean": round(float(series.mean()), 2), "minimum": round(float(series.min()), 2), "maximum": round(float(series.max()), 2), "median": round(float(series.median()), 2), "std": round(float(series.std()), 2), "distribution": [{"range": f"{left:.1f}–{right:.1f}", "count": int(count)} for count, left, right in zip(*_histogram(series))]}


def _histogram(series):
    import numpy as np
    counts, edges = np.histogram(series.dropna(), bins=10)
    return counts, edges[:-1], edges[1:]
