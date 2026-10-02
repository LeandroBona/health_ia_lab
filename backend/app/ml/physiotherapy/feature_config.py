"""Explicit predictor allowlist: no identifier and no target leakage."""
from app.schemas.physiotherapy import PatientFeatures, RESULTS

FEATURES = list(PatientFeatures.model_fields)
CATEGORICAL_FEATURES = ["sexo", "tipo_lesao"]
NUMERIC_FEATURES = [column for column in FEATURES if column not in CATEGORICAL_FEATURES]
TARGET = "resultado"
CLASSES = RESULTS
RANDOM_STATE = 42
MODEL_NOTICE = "Este modelo foi treinado exclusivamente com dados sintéticos e relações artificialmente construídas para fins educacionais. Seus resultados não possuem validade clínica."

FEATURE_LABELS = {
    "idade": "Idade", "sexo": "Sexo", "tipo_lesao": "Tipo de lesão",
    "tempo_lesao_dias": "Tempo da lesão", "dor_inicial": "Dor inicial",
    "dor_atual": "Dor atual", "mobilidade_inicial": "Mobilidade inicial",
    "mobilidade_atual": "Mobilidade atual", "forca_muscular": "Força muscular",
    "sessoes_previstas": "Sessões previstas", "sessoes_realizadas": "Sessões realizadas",
    "faltas": "Número de faltas", "adesao_exercicios": "Adesão aos exercícios",
    "comorbidades": "Comorbidades", "indice_funcional_inicial": "Índice funcional inicial",
    "indice_funcional_atual": "Índice funcional atual",
}

RESULT_LABELS = {
    "recuperacao_adequada": "Recuperação adequada",
    "recuperacao_lenta": "Recuperação lenta",
    "abandono": "Abandono",
}

EXPLANATION_NOTICE = (
    "Contribuições SHAP descrevem o comportamento matemático do modelo para dados sintéticos. "
    "Associação no modelo não demonstra causalidade nem possui interpretação clínica."
)
