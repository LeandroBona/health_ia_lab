from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database.session import get_db
from app.models.physiotherapy import PhysiotherapyPatient
from app.schemas.physiotherapy import ConfirmImportRequest, INJURIES, Injury, NUMERIC_COLUMNS, REQUIRED_COLUMNS, RESULTS, RegenerateRequest, Result, SEXES, Sex, PatientData
from app.services import physiotherapy_dataset as datasets
from app.services.physiotherapy_service import explore, list_patients, stats
from app.services.physiotherapy_validation import DatasetError, MAX_BYTES

router = APIRouter(prefix="/fisioterapia", tags=["fisioterapia"])


@router.get("/schema")
def schema():
    return {"columns": REQUIRED_COLUMNS, "numeric_columns": NUMERIC_COLUMNS, "sexes": SEXES, "injuries": INJURIES, "results": RESULTS, "fields": PatientData.model_json_schema()["properties"]}


@router.get("/patients")
def patients(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), search: str | None = Query(None, max_length=40), resultado: Result | None = None, tipo_lesao: Injury | None = None, sexo: Sex | None = None, db: Session = Depends(get_db)):
    return list_patients(db, page, page_size, search, resultado, tipo_lesao, sexo)


@router.get("/patients/{patient_id}", response_model=PatientData)
def patient(patient_id: str, db: Session = Depends(get_db)):
    item = db.get(PhysiotherapyPatient, patient_id)
    if item is None:
        raise DatasetError("Paciente não encontrado.", 404)
    return item


@router.get("/stats")
def statistics(db: Session = Depends(get_db)):
    return stats(db)


@router.get("/explore")
def exploration(column: str = "idade", db: Session = Depends(get_db)):
    return explore(db, column)


@router.get("/dataset")
def dataset(db: Session = Depends(get_db)):
    return datasets.dataset_info(db)


@router.get("/dataset/download/{format}")
def download(format: str):
    if format not in {"csv", "xlsx"}:
        raise DatasetError("Formato não suportado.", 404)
    filename = f"pacientes_fisioterapia.{format}"
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
def confirm(body: ConfirmImportRequest, db: Session = Depends(get_db)):
    return datasets.confirm_import(db, body.token)


@router.post("/dataset/regenerate")
def regenerate(body: RegenerateRequest, db: Session = Depends(get_db)):
    if not body.confirm:
        raise DatasetError("Confirme a substituição dos arquivos e pacientes do dataset padrão. Pacientes importados serão preservados.", 409)
    return datasets.regenerate_dataset(db, body.size, body.seed)
