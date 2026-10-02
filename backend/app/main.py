from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.routes import router as api_router
from app.core.config import settings
from app.database.session import engine, SessionLocal
from app.database.migrate import run_migrations
from app.api.physiotherapy import router as physiotherapy_router
from app.services.physiotherapy_dataset import initialize_dataset
from app.services.physiotherapy_validation import DatasetError
from app.api.physiotherapy_ml import router as ml_router
from app.ml.physiotherapy.model_manager import initialize_model
from app.api.nursing import router as nursing_router
from app.services.nursing_dataset import initialize_dataset as initialize_nursing_dataset
from app.ml.nursing.anomaly_service import initialize_model as initialize_nursing_model
from app.api.pharmacy import router as pharmacy_router
from app.services.pharmacy_dataset import initialize_datasets as initialize_pharmacy_datasets
from app.ml.pharmacy.adherence.model_manager import initialize_model as initialize_adherence_model
from app.ml.pharmacy.demand.model_manager import initialize_model as initialize_demand_model
from app.api.veterinary import router as veterinary_router
from app.services.veterinary_dataset import initialize_datasets as initialize_veterinary_datasets
from app.ml.veterinary.classification.model_manager import initialize_model as initialize_veterinary_model
from app.ml.veterinary.anomaly.model_manager import initialize_model as initialize_veterinary_anomaly_model
from app.api.psychology import router as psychology_router
from app.services.psychology_dataset import initialize_dataset as initialize_psychology_dataset
from app.ml.psychology.model_manager import initialize_model as initialize_psychology_model
from app.api.generative import router as generative_router
from app.api.platform import router as platform_router
from app.api.history import router as history_router
from app.api.classroom import router as classroom_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Prepare the local database while keeping room for future models."""
    run_migrations(engine)
    with SessionLocal() as db:
        initialize_dataset(db)
        initialize_model(db)
        initialize_nursing_dataset(db)
        initialize_nursing_model(db)
        initialize_pharmacy_datasets(db)
        initialize_adherence_model(db)
        initialize_demand_model(db)
        initialize_veterinary_datasets(db)
        initialize_veterinary_model(db)
        initialize_veterinary_anomaly_model(db)
        initialize_psychology_dataset(db)
        initialize_psychology_model(db)
    yield


app = FastAPI(
    title=settings.app_name,
    description="API educacional para demonstrações de IA aplicada à saúde.",
    version="0.8.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Content-Type"],
)

app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(physiotherapy_router, prefix=settings.api_prefix)
app.include_router(ml_router, prefix=settings.api_prefix)
app.include_router(nursing_router, prefix=settings.api_prefix)
app.include_router(pharmacy_router, prefix=settings.api_prefix)
app.include_router(veterinary_router, prefix=settings.api_prefix)
app.include_router(psychology_router, prefix=settings.api_prefix)
app.include_router(generative_router, prefix=settings.api_prefix)
app.include_router(platform_router, prefix=settings.api_prefix)
app.include_router(history_router, prefix=settings.api_prefix)
app.include_router(classroom_router, prefix=settings.api_prefix)


@app.exception_handler(DatasetError)
async def dataset_error_handler(_, exc: DatasetError):
    return JSONResponse(status_code=exc.status, content=exc.body)


@app.exception_handler(RequestValidationError)
async def request_error_handler(_, exc: RequestValidationError):
    messages = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"] if part != "body") or "dados"
        context = error.get("ctx", {})
        kind = error["type"]
        if kind == "greater_than_equal":
            reason = f"o mínimo é {context['ge']}"
        elif kind == "less_than_equal":
            reason = f"o máximo é {context['le']}"
        elif kind == "missing":
            reason = "campo obrigatório"
        elif kind == "extra_forbidden":
            reason = "campo não permitido"
        elif kind == "value_error":
            reason = str(context.get("error", "valor inválido"))
        elif kind.startswith("int"):
            reason = "informe um número inteiro"
        else:
            reason = "valor fora do formato ou das categorias permitidas"
        messages.append(f"{field}: {reason}")
    return JSONResponse(status_code=422, content={"success": False, "message": "Parâmetros inválidos. " + "; ".join(messages)})


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "application": settings.app_name,
        "documentation": "/docs",
    }
