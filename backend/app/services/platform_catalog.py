"""Read-only adapters over existing module metadata. Never trains models."""
from collections import Counter
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.physiotherapy import PhysiotherapyDataset, PhysiotherapyPatient
from app.models.nursing import NursingDataset, NursingPatient, NursingMeasurement
from app.models.pharmacy import PharmacyDataset, PharmacyAdherencePatient, PharmacyDemandRecord
from app.models.veterinary import VeterinaryDataset, VeterinaryAnimal, VeterinaryFollowUp
from app.models.psychology import PsychologyDataset, PsychologyRecord
from app.ml.physiotherapy import model_manager as physio
from app.ml.nursing import anomaly_service as nursing
from app.ml.pharmacy.adherence import model_manager as adherence
from app.ml.pharmacy.demand import model_manager as demand
from app.ml.veterinary.classification import model_manager as vet_class
from app.ml.veterinary.anomaly import model_manager as vet_anomaly
from app.ml.psychology import model_manager as psychology
from app.services.llm.llm_service import LLMService
from app.services.physiotherapy_validation import DatasetError


@dataclass(frozen=True)
class DatasetSpec:
    id: str
    name: str
    module: str
    kind: str
    model: type
    metadata_model: type
    metadata_id: str
    download_base: str
    view_path: str
    import_path: str
    explore_path: str
    related_model: type | None = None
    time_column: str | None = None
    category_column: str | None = None


DATASETS = [
    DatasetSpec("physiotherapy", "Pacientes de Fisioterapia", "fisioterapia", "tabular", PhysiotherapyPatient, PhysiotherapyDataset, "default-physiotherapy", "/api/fisioterapia/dataset/download", "/fisioterapia/explorar", "/fisioterapia/importar", "/fisioterapia/explorar", category_column="resultado"),
    DatasetSpec("nursing", "Monitoramento de Enfermagem", "enfermagem", "temporal", NursingMeasurement, NursingDataset, "default-nursing", "/api/enfermagem/dataset/download", "/enfermagem/dataset", "/enfermagem/importar", "/enfermagem/dataset/temporal", NursingPatient, "timestamp", "classification"),
    DatasetSpec("pharmacy-adherence", "Adesão em Farmácia", "farmacia", "tabular", PharmacyAdherencePatient, PharmacyDataset, "default-pharmacy-adesao", "/api/farmacia/adesao/dataset/download", "/farmacia/adesao", "/farmacia/adesao/importar", "/farmacia/adesao", category_column="categoria_adesao"),
    DatasetSpec("pharmacy-demand", "Demanda em Farmácia", "farmacia", "temporal", PharmacyDemandRecord, PharmacyDataset, "default-pharmacy-demanda", "/api/farmacia/demanda/dataset/download", "/farmacia/demanda", "/farmacia/demanda/importar", "/farmacia/demanda", time_column="period"),
    DatasetSpec("veterinary-animals", "Animais fictícios", "veterinaria", "tabular", VeterinaryAnimal, VeterinaryDataset, "default-veterinary-animals", "/api/veterinaria/animals/dataset/download", "/veterinaria", "/veterinaria/importar", "/veterinaria", category_column="evolucao"),
    DatasetSpec("veterinary-followups", "Acompanhamentos veterinários", "veterinaria", "temporal", VeterinaryFollowUp, VeterinaryDataset, "default-veterinary-followups", "/api/veterinaria/followups/dataset/download", "/veterinaria", "/veterinaria/importar", "/veterinaria", time_column="timestamp", category_column="classification"),
    DatasetSpec("psychology", "Relatos de Psicologia", "psicologia", "text", PsychologyRecord, PsychologyDataset, "default-psychology", "/api/psicologia/dataset/download", "/psicologia", "/psicologia/importar", "/psicologia", category_column="tema_principal"),
]


def count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def dataset_row(db: Session, spec: DatasetSpec) -> dict:
    metadata = db.get(spec.metadata_model, spec.metadata_id)
    columns = [column.name for column in spec.model.__table__.columns if column.name not in {"dataset_id", "id", "classification", "anomaly_score", "analyzed_model_version"}]
    return {"id": spec.id, "name": spec.name, "module": spec.module, "kind": spec.kind,
            "records": count(db, spec.model), "related_records": count(db, spec.related_model) if spec.related_model else None,
            "columns": columns, "column_count": len(columns), "created_at": getattr(metadata, "created_at", None),
            "seed": getattr(metadata, "seed", None), "synthetic": True,
            "formats": ["csv", "xlsx"], "download_urls": {fmt: f"{spec.download_base}/{fmt}" for fmt in ("csv", "xlsx")},
            "view_path": spec.view_path, "import_path": spec.import_path, "explore_path": spec.explore_path,
            "can_regenerate": spec.id == "physiotherapy"}


def datasets(db: Session) -> list[dict]:
    return [dataset_row(db, spec) for spec in DATASETS]


def dataset_detail(db: Session, dataset_id: str) -> dict:
    spec = next((item for item in DATASETS if item.id == dataset_id), None)
    if spec is None:
        raise DatasetError("Dataset não encontrado.", 404)
    base = dataset_row(db, spec)
    rows = db.scalars(select(spec.model).limit(20)).all()
    preview = [{key: getattr(row, key) for key in base["columns"]} for row in rows]
    base["preview"] = preview
    base["missing_values"] = {key: db.scalar(select(func.count()).select_from(spec.model).where(getattr(spec.model, key).is_(None))) or 0 for key in base["columns"]}
    base["missing_total"] = sum(base["missing_values"].values())
    numeric = [column for column in spec.model.__table__.columns if column.name in base["columns"] and column.type.python_type in (int, float)]
    base["statistics"] = {column.name: {"mean": db.scalar(select(func.avg(column))) or 0, "minimum": db.scalar(select(func.min(column))), "maximum": db.scalar(select(func.max(column)))} for column in numeric[:6]}
    if spec.category_column:
        col = getattr(spec.model, spec.category_column)
        base["distribution"] = {str(value): amount for value, amount in db.execute(select(col, func.count()).group_by(col)).all()}
    if spec.time_column:
        col = getattr(spec.model, spec.time_column)
        first, last = db.execute(select(func.min(col), func.max(col))).one()
        base["time_range"] = {"first": first, "last": last}
    if spec.kind == "text":
        from app.ml.psychology.preprocessing import content_tokens
        texts = db.scalars(select(PsychologyRecord.texto)).all()
        base["average_text_length"] = round(sum(map(len, texts)) / len(texts), 1) if texts else 0
        base["terms"] = [{"term": term, "count": value} for term, value in Counter(token for text in texts for token in content_tokens(text)).most_common(10)]
    return base


MODEL_SPECS = [
    ("physiotherapy-classification", "Modelo preditivo — Fisioterapia", "fisioterapia", "classification", "F1 Macro", "/fisioterapia/modelo", physio),
    ("nursing-anomaly", "Detecção de anomalias — Enfermagem", "enfermagem", "anomaly", "F1", "/enfermagem/modelo", nursing),
    ("pharmacy-adherence", "Classificação de adesão — Farmácia", "farmacia", "classification", "F1 Macro", "/farmacia/adesao/modelo", adherence),
    ("pharmacy-demand", "Previsão de demanda — Farmácia", "farmacia", "regression", "MAE", "/farmacia/demanda/modelo", demand),
    ("veterinary-classification", "Modelo preditivo — Veterinária", "veterinaria", "classification", "F1 Macro", "/veterinaria/modelo", vet_class),
    ("veterinary-anomaly", "Detecção de anomalias — Veterinária", "veterinaria", "anomaly", "Fração de anomalias", "/veterinaria/modelo", vet_anomaly),
    ("psychology-classification", "Classificação temática — Psicologia", "psicologia", "nlp", "F1 Macro", "/psicologia/modelo", psychology),
    ("psychology-clustering", "Agrupamento de textos — Psicologia", "psicologia", "clustering", "Grupos", "/psicologia/modelo", psychology),
    ("psychology-similarity", "Similaridade textual — Psicologia", "psicologia", "similarity", "Textos indexados", "/psicologia/modelo", psychology),
]


def models() -> list[dict]:
    result = []
    for id_, name, module, type_, metric_label, path, manager in MODEL_SPECS:
        bundle = getattr(manager, "_bundle", None)
        metadata = bundle.get("metadata", {}) if bundle else {}
        metrics = metadata.get("metrics") or metadata.get("evaluation") or {}
        metric_key = {"F1 Macro": "f1_macro", "F1": "f1", "MAE": "mae", "Fração de anomalias": "anomaly_fraction"}.get(metric_label)
        metric_value = metadata.get("cluster_count") if type_ == "clustering" else metadata.get("records") if type_ == "similarity" else metrics.get(metric_key) if metric_key else None
        algorithm = metadata.get("cluster_algorithm") if type_ == "clustering" else metadata.get("similarity_algorithm") if type_ == "similarity" else metadata.get("selected_model") or metadata.get("algorithm") or metadata.get("name")
        result.append({"id": id_, "name": name, "module": module, "type": type_, "algorithm": algorithm,
                       "status": "ready" if bundle else "unavailable", "version": metadata.get("version"),
                       "trained_at": metadata.get("trained_at") or metadata.get("date"),
                       "dataset": metadata.get("dataset") or metadata.get("dataset_source"),
                       "metric_name": metric_key or metric_label, "metric_value": metric_value,
                       "detail_path": path})
    result.append({"id": "vision-pose", "name": "Estimativa de pose", "module": "visao-computacional", "type": "vision", "algorithm": "MediaPipe Pose Landmarker", "status": "available", "version": "1.0.1", "trained_at": None, "dataset": "Webcam local", "metric_name": None, "metric_value": None, "detail_path": "/visao-computacional/laboratorio"})
    llm = LLMService().status()
    result.append({"id": "generative-explanation", "name": "Explicação textual", "module": "ia-generativa", "type": "generative", "algorithm": llm["model"] if llm["mode"] == "online" else "LocalTemplateProvider", "status": "available" if llm["mode"] == "online" else "offline", "version": None, "trained_at": None, "dataset": "Resultados estruturados sintéticos", "metric_name": None, "metric_value": None, "detail_path": "/ia-generativa"})
    return result
