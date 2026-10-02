from collections import Counter, defaultdict
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.data_generators.psychology import COLUMNS, THEMES
from app.database.session import get_db
from app.ml.psychology import model_manager
from app.ml.psychology.classification import classify_text
from app.ml.psychology.clustering import approximate_group
from app.ml.psychology.keywords import extract_keywords
from app.ml.psychology.preprocessing import content_tokens, processing_details
from app.ml.psychology.similarity import find_similar
from app.models.psychology import PsychologyRecord
from app.schemas.psychology import ConfirmImport, TextInput
from app.services import psychology_dataset as datasets
from app.services.physiotherapy_validation import DatasetError, MAX_BYTES
from app.services.analysis_history import record as record_history

router = APIRouter(prefix="/psicologia", tags=["psicologia"])
NOTICE = "Este módulo analisa características linguísticas de textos sintéticos e não realiza diagnóstico psicológico, avaliação clínica ou interpretação da condição emocional de uma pessoa real."


def row_dict(item: PsychologyRecord) -> dict:
    return {key: getattr(item, key) for key in COLUMNS}


def analyze_text(text: str) -> dict:
    bundle = model_manager.snapshot()
    keywords = extract_keywords(text, bundle["vectorizer"])
    return {"original_text": text, "keywords": keywords, "classification": classify_text(text, bundle),
            "similar": find_similar(text, bundle), "cluster": approximate_group(text, bundle),
            "processing": processing_details(text, bundle["metadata"]["features"]),
            "tfidf": keywords[:10], "notice": NOTICE}


@router.get("/records")
def records(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), record_id: str | None = None,
            tema: str | None = None, contexto: str | None = None, db: Session = Depends(get_db)):
    query = select(PsychologyRecord)
    if record_id:
        query = query.where(PsychologyRecord.record_id.contains(record_id))
    if tema:
        query = query.where(PsychologyRecord.tema_principal == tema)
    if contexto:
        query = query.where(PsychologyRecord.contexto == contexto)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(PsychologyRecord.record_id).offset((page - 1) * page_size).limit(page_size)).all()
    predictions = model_manager.snapshot()["pipeline"].predict([item.texto for item in items]) if items else []
    return {"items": [{**row_dict(item), "tema_previsto": str(prediction)} for item, prediction in zip(items, predictions)],
            "total": total, "page": page, "page_size": page_size}


@router.get("/records/{record_id}")
def record(record_id: str, db: Session = Depends(get_db)):
    item = db.get(PsychologyRecord, record_id)
    if item is None:
        raise DatasetError("Relato sintético não encontrado.", 404)
    analysis = analyze_text(item.texto)
    return {**row_dict(item), "analysis": analysis, "correct": analysis["classification"]["prediction"] == item.tema_principal}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    def counts(column):
        return {str(value): count for value, count in db.execute(select(column, func.count()).group_by(column)).all()}
    bundle = model_manager.snapshot()
    return {"records": db.scalar(select(func.count()).select_from(PsychologyRecord)) or 0,
            "themes": len(THEMES), "clusters": bundle["metadata"]["cluster_count"],
            "model": bundle["metadata"]["algorithm"], "f1_macro": bundle["metadata"]["metrics"]["f1_macro"],
            "theme_distribution": counts(PsychologyRecord.tema_principal), "context_distribution": counts(PsychologyRecord.contexto),
            "cluster_distribution": bundle["metadata"]["cluster_sizes"],
            "average_text_length": round(float(db.scalar(select(func.avg(func.length(PsychologyRecord.texto)))) or 0), 1), "notice": NOTICE}


@router.get("/terms")
def terms(limit: int = Query(10, ge=1, le=50), tema: str | None = None, contexto: str | None = None, db: Session = Depends(get_db)):
    if tema and tema not in THEMES:
        raise DatasetError("Tema não reconhecido.")
    query = select(PsychologyRecord)
    if tema:
        query = query.where(PsychologyRecord.tema_principal == tema)
    if contexto:
        query = query.where(PsychologyRecord.contexto == contexto)
    items = db.scalars(query).all()
    words, bigrams = Counter(), Counter()
    by_theme: dict[str, Counter] = defaultdict(Counter)
    for item in items:
        tokens = content_tokens(item.texto)
        words.update(tokens)
        bigrams.update(" ".join(pair) for pair in zip(tokens, tokens[1:]))
        by_theme[item.tema_principal].update(tokens)
    format_counts = lambda values: [{"term": term, "count": count} for term, count in values.most_common(limit)]
    return {"total_records": len(items), "words": format_counts(words), "bigrams": format_counts(bigrams),
            "by_theme": {theme: format_counts(values) for theme, values in sorted(by_theme.items())}}


@router.get("/clusters")
def clusters():
    return {"algorithm": "TF-IDF + KMeans", "groups": model_manager.snapshot()["cluster_summary"],
            "explanation": "O algoritmo não recebeu os temas antes. Ele agrupou automaticamente textos matematicamente semelhantes."}


@router.get("/model")
def model():
    return model_manager.info()


@router.get("/model/evaluation")
def evaluation():
    info = model_manager.info()
    return {"metrics": info["metrics"], "labels": info["labels"], "confusion_matrix": info["confusion_matrix"], "note": info["evaluation_note"]}


@router.post("/model/train")
def train(db: Session = Depends(get_db)):
    return model_manager.train_model(db)


@router.post("/keywords")
def keywords(body: TextInput):
    return {"keywords": extract_keywords(body.text, model_manager.snapshot()["vectorizer"])}


@router.post("/classify")
def classify(body: TextInput):
    return classify_text(body.text, model_manager.snapshot())


@router.post("/similarity")
def similarity(body: TextInput):
    return {"results": find_similar(body.text, model_manager.snapshot())}


@router.post("/analyze")
def analyze(body: TextInput, db: Session = Depends(get_db)):
    result = analyze_text(body.text)
    metadata = model_manager.snapshot()["metadata"]
    event = record_history(db, module="psicologia", analysis_type="psychology_nlp", model_name=metadata["algorithm"], model_version=metadata["version"], result_summary=f"Tema linguístico: {result['classification']['prediction']}; grupo: {result['cluster']['label']}.")
    return result


@router.get("/dataset/download/{format_}")
def download(format_: str):
    path = datasets.default_file(format_)
    if not path.is_file():
        raise DatasetError("Arquivo padrão indisponível.", 404)
    return FileResponse(path, filename=path.name)


@router.post("/upload/preview")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read(MAX_BYTES + 1)
        filename = Path((file.filename or "arquivo").replace("\\", "/")).name[:255]
        return await run_in_threadpool(datasets.create_preview, db, content, filename)
    finally:
        await file.close()


@router.post("/upload/confirm")
def confirm(body: ConfirmImport, db: Session = Depends(get_db)):
    return datasets.confirm_import(db, body.token)
