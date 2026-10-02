from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.analysis_history import AnalysisHistory
from app.services.analysis_history import VALID_TYPES, list_items, record, serialize

router = APIRouter(prefix="/history", tags=["histórico educacional"])


class VisionSessionEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    movements: int = Field(ge=0, le=100000)
    samples: int = Field(ge=1, le=1200)
    joint: Literal["leftElbow", "rightElbow", "leftKnee", "rightKnee"]
    reference: str = Field(min_length=2, max_length=60, pattern=r"^[A-Za-z0-9_-]+$")


@router.post("/vision-session")
def vision_session(body: VisionSessionEvent, db: Session = Depends(get_db)):
    item = record(db, module="visao-computacional", analysis_type="vision_session",
                  model_name="MediaPipe Pose Landmarker", model_version="1.0.1",
                  record_reference=body.reference,
                  result_summary=f"Sessão numérica: {body.samples} amostras, {body.movements} movimentos; articulação {body.joint}.")
    return serialize(item)


@router.get("")
def history(module: str | None = None, analysis_type: str | None = None,
            model: str | None = Query(None, max_length=100), date_from: date | None = None,
            date_to: date | None = None, page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    if analysis_type and analysis_type not in VALID_TYPES:
        raise HTTPException(422, detail="Tipo de análise inválido.")
    return list_items(db, module=module, analysis_type=analysis_type, model=model,
                      date_from=date_from.isoformat() if date_from else None,
                      date_to=date_to.isoformat() if date_to else None, page=page, page_size=page_size)


@router.get("/{history_id}")
def detail(history_id: str, db: Session = Depends(get_db)):
    item = db.get(AnalysisHistory, history_id)
    if item is None:
        raise HTTPException(404, detail="Análise não encontrada.")
    return serialize(item)
