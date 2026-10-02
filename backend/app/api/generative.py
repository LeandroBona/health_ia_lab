import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.session import get_db
from app.services.analysis_history import record as record_history
from app.models.analysis_history import AnalysisHistory

from app.services.llm.llm_service import LLMService
from app.services.llm.openai_provider import ProviderError
from app.services.llm.prompt_builder import SYSTEM_PROMPT, build_prompt
from app.services.llm.schemas import ContentRequest, ExplainRequest, PromptFields, QuestionRequest
from app.services.llm.base import GenerationInput

router = APIRouter(prefix="/generative", tags=["IA generativa"])
logger = logging.getLogger(__name__)


@router.get("/status")
def status():
    return LLMService().status()


@router.post("/explain")
def explain(body: ExplainRequest, db: Session = Depends(get_db)):
    response = LLMService().explain(body)
    source_id = body.source_history_id
    if source_id is None and body.record_reference:
        source_types = {
            ("fisioterapia", "prediction"): ("physiotherapy_prediction",),
            ("enfermagem", "anomaly"): ("nursing_anomaly",),
            ("farmacia", "prediction"): ("pharmacy_adherence",),
            ("farmacia", "demand"): ("pharmacy_demand",),
            ("veterinaria", "prediction"): ("veterinary_prediction",),
            ("veterinaria", "anomaly"): ("veterinary_anomaly",),
            ("psicologia", "nlp"): ("psychology_nlp",),
        }.get((body.module, body.analysis_type), ())
        source = db.scalar(select(AnalysisHistory).where(
            AnalysisHistory.module == body.module,
            AnalysisHistory.record_reference == body.record_reference,
            AnalysisHistory.analysis_type.in_(source_types),
        ).order_by(AnalysisHistory.created_at.desc()).limit(1))
        source_id = source.id if source else None
    event = record_history(db, module="ia-generativa", analysis_type="generative_explanation", model_name=response["provider"], record_reference=body.record_reference, source_history_id=source_id, result_summary=f"Explicação textual de {body.module}/{body.analysis_type}; provider {response['provider']}. Conteúdo não armazenado.")
    return {**response, "history_id": event.id}


@router.post("/content")
def content(body: ContentRequest, db: Session = Depends(get_db)):
    response = LLMService().educational(body)
    record_history(db, module="ia-generativa", analysis_type="generative_content", model_name=response["provider"], result_summary=f"Conteúdo didático sobre {body.topic}; provider {response['provider']}.")
    return response


@router.post("/question")
def question(body: QuestionRequest, db: Session = Depends(get_db)):
    response = LLMService().question(body)
    record_history(db, module="ia-generativa", analysis_type="generative_question", model_name=response["provider"], result_summary=f"Pergunta educacional sobre {body.topic}; provider {response['provider']}.")
    return response


@router.post("/prompt/execute")
def execute_prompt(body: PromptFields):
    service = LLMService()
    if not service.external.is_available():
        raise HTTPException(503, detail="A execução de prompts exige um provider externo configurado. O construtor segue disponível.")
    # Lab text is user-authored and bounded by PromptFields, never a dataset or raw database export.
    try:
        output = service.external.generate(GenerationInput(task="prompt", details=build_prompt(body), creativity=body.creativity))
        if len(output) > 5000:
            output = output[:5000]
        logger.info("generative_prompt provider=openai success=true")
        return service._response(service.external.get_provider_name(), output, "online")
    except ProviderError as exc:
        logger.warning("generative_prompt provider=openai success=false code=%s", exc.code)
        raise HTTPException(503, detail=f"Não foi possível gerar a resposta externa: {exc} Use a explicação local nos módulos.") from None
