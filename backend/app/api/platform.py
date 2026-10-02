from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.analysis_history import list_items
from app.services.llm.llm_service import LLMService
from app.services.platform_catalog import dataset_detail, datasets, models

router = APIRouter(tags=["plataforma"])


@router.get("/models")
def all_models():
    return {"items": models()}


@router.get("/datasets")
def all_datasets(db: Session = Depends(get_db)):
    return {"items": datasets(db)}


@router.get("/datasets/{dataset_id}")
def one_dataset(dataset_id: str, db: Session = Depends(get_db)):
    return dataset_detail(db, dataset_id)


@router.get("/system/status")
def system_status(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "error"
    dataset_items = datasets(db) if database == "ok" else []
    model_items = models()
    return {"backend": "ok", "database": database,
            "datasets": {"status": "available" if dataset_items else "empty", "count": len(dataset_items)},
            "models": {"status": "available" if any(item["status"] == "ready" for item in model_items) else "unavailable", "count": len(model_items)},
            "llm": LLMService().status(), "vision": {"status": "browser", "description": "Processamento local; disponibilidade da câmera verificada no navegador."}}
