import pandas as pd
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.physiotherapy import PhysiotherapyPatient as Patient
from app.schemas.physiotherapy import CATEGORICAL_COLUMNS, REQUIRED_COLUMNS, RESULTS, PatientData
from app.services.physiotherapy_validation import DatasetError


def list_patients(db: Session, page: int, page_size: int, search: str | None, resultado: str | None, tipo_lesao: str | None, sexo: str | None) -> dict:
    conditions = []
    if search:
        conditions.append(Patient.patient_id.icontains(search.strip(), autoescape=True))
    for field, value in [(Patient.resultado, resultado), (Patient.tipo_lesao, tipo_lesao), (Patient.sexo, sexo)]:
        if value:
            conditions.append(field == value)
    total = db.scalar(select(func.count()).select_from(Patient).where(*conditions))
    patients = db.scalars(select(Patient).where(*conditions).order_by(Patient.patient_id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [PatientData.model_validate(patient).model_dump() for patient in patients], "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}


def stats(db: Session) -> dict:
    row = db.execute(select(func.count(Patient.patient_id), func.avg(Patient.idade), func.avg(Patient.dor_inicial), func.avg(Patient.dor_atual), func.avg(Patient.adesao_exercicios))).one()
    results = dict.fromkeys(RESULTS, 0)
    results.update(dict(db.execute(select(Patient.resultado, func.count()).group_by(Patient.resultado)).all()))
    injury_counts = db.execute(select(Patient.tipo_lesao, func.count()).group_by(Patient.tipo_lesao).order_by(Patient.tipo_lesao)).all()
    bands = case((Patient.adesao_exercicios <= 25, "0–25%"), (Patient.adesao_exercicios <= 50, "26–50%"), (Patient.adesao_exercicios <= 75, "51–75%"), else_="76–100%")
    counts = dict(db.execute(select(bands, func.count()).group_by(bands)).all())
    return {
        "total_patients": row[0], "average_age": round(row[1] or 0, 1),
        "average_pain_initial": round(row[2] or 0, 1), "average_pain_current": round(row[3] or 0, 1),
        "average_adherence": round(row[4] or 0, 1), "results": results, "registered_results": sum(results.values()),
        "injuries": [{"name": name, "count": count} for name, count in injury_counts],
        "adherence_distribution": [{"name": name, "count": counts.get(name, 0)} for name in ["0–25%", "26–50%", "51–75%", "76–100%"]],
    }


def explore(db: Session, column: str) -> dict:
    if column not in REQUIRED_COLUMNS:
        raise DatasetError("Selecione uma coluna válida.")
    values = pd.Series(db.scalars(select(getattr(Patient, column))).all())
    result = {"column": column, "count": int(values.count()), "missing": int(values.isna().sum()), "unique": int(values.nunique())}
    if column in CATEGORICAL_COLUMNS:
        counts = values.value_counts().sort_index()
        result.update({"kind": "categorical", "distribution": [{"name": str(name), "count": int(count)} for name, count in counts.head(30).items()], "truncated": len(counts) > 30})
    else:
        clean = pd.to_numeric(values.dropna())
        summary = {"mean": None, "min": None, "max": None, "median": None, "std": None}
        distribution = []
        if len(clean):
            summary = {key: round(float(value), 2) for key, value in {"mean": clean.mean(), "min": clean.min(), "max": clean.max(), "median": clean.median(), "std": clean.std(ddof=0)}.items()}
            if clean.nunique() <= 10:
                distribution = [{"name": str(name), "count": int(count)} for name, count in clean.value_counts().sort_index().items()]
            else:
                grouped = pd.cut(clean, bins=10, include_lowest=True).value_counts(sort=False)
                distribution = [{"name": f"{interval.left:.1f} a {interval.right:.1f}", "count": int(count)} for interval, count in grouped.items()]
        result.update({"kind": "numeric", **summary, "distribution": distribution, "truncated": False})
    return result
