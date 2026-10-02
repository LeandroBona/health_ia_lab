from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db

from app.core.config import settings
from app.schemas.dashboard import DashboardResponse
from app.schemas.health import HealthResponse
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", application=settings.app_name)


@router.get("/dashboard", response_model=DashboardResponse, tags=["dashboard"])
def dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    return get_dashboard_summary(db)
