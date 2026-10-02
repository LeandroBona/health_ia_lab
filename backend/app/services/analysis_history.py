import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analysis_history import AnalysisHistory

VALID_MODULES = {"fisioterapia", "enfermagem", "farmacia", "veterinaria", "psicologia", "visao-computacional", "ia-generativa"}
VALID_TYPES = {
    "physiotherapy_prediction", "physiotherapy_simulation", "nursing_anomaly", "pharmacy_adherence",
    "pharmacy_demand", "veterinary_prediction", "veterinary_anomaly", "psychology_nlp",
    "vision_session", "generative_explanation", "generative_content", "generative_question",
}
REFERENCE = re.compile(r"^[A-Za-z0-9_-]{2,60}$")


def record(db: Session, *, module: str, analysis_type: str, model_name: str,
           result_summary: str, model_version: str | None = None,
           record_reference: str | None = None, source_history_id: str | None = None) -> AnalysisHistory:
    if module not in VALID_MODULES or analysis_type not in VALID_TYPES:
        raise ValueError("Módulo ou tipo de análise inválido.")
    if record_reference is not None and not REFERENCE.fullmatch(record_reference):
        raise ValueError("Referência inválida.")
    if source_history_id is not None and db.get(AnalysisHistory, source_history_id) is None:
        source_history_id = None
    item = AnalysisHistory(
        id=str(uuid.uuid4()), module=module, analysis_type=analysis_type,
        model_name=model_name[:100], model_version=model_version[:30] if model_version else None,
        record_reference=record_reference, result_summary=result_summary[:255],
        created_at=datetime.now(timezone.utc).isoformat(), source_history_id=source_history_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def serialize(item: AnalysisHistory) -> dict:
    return {key: getattr(item, key) for key in ("id", "module", "analysis_type", "model_name", "model_version", "record_reference", "result_summary", "created_at", "source_history_id")}


def list_items(db: Session, *, module: str | None, analysis_type: str | None,
               model: str | None, date_from: str | None, date_to: str | None,
               page: int, page_size: int) -> dict:
    query = select(AnalysisHistory)
    if module:
        query = query.where(AnalysisHistory.module == module)
    if analysis_type:
        query = query.where(AnalysisHistory.analysis_type == analysis_type)
    if model:
        query = query.where(AnalysisHistory.model_name.contains(model))
    if date_from:
        query = query.where(AnalysisHistory.created_at >= date_from)
    if date_to:
        query = query.where(AnalysisHistory.created_at < date_to + "T23:59:59.999999+00:00")
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(AnalysisHistory.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize(item) for item in rows], "total": total, "page": page, "page_size": page_size}
