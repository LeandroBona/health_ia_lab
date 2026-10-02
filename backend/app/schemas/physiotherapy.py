"""Single source of truth for the educational dataset contract."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Sex = Literal["Masculino", "Feminino", "Outro"]
Injury = Literal["Joelho", "Ombro", "Coluna lombar", "Tornozelo", "Quadril", "Cotovelo", "Punho", "Lesão muscular", "Pós-operatório", "Outros"]
Result = Literal["recuperacao_adequada", "recuperacao_lenta", "abandono"]
SEXES = list(Sex.__args__)
INJURIES = list(Injury.__args__)
RESULTS = list(Result.__args__)


class PatientFeatures(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def reject_booleans(cls, value):
        if isinstance(value, bool):
            raise ValueError("Utilize um valor numérico ou uma categoria, não verdadeiro/falso.")
        return value

    idade: int = Field(ge=18, le=85)
    sexo: Sex
    tipo_lesao: Injury
    tempo_lesao_dias: int = Field(ge=1, le=730)
    dor_inicial: int = Field(ge=0, le=10)
    dor_atual: int = Field(ge=0, le=10)
    mobilidade_inicial: int = Field(ge=0, le=100)
    mobilidade_atual: int = Field(ge=0, le=100)
    forca_muscular: int = Field(ge=1, le=5)
    sessoes_previstas: int = Field(ge=5, le=30)
    sessoes_realizadas: int = Field(ge=0, le=30)
    faltas: int = Field(ge=0, le=30)
    adesao_exercicios: int = Field(ge=0, le=100)
    comorbidades: int = Field(ge=0, le=5)
    indice_funcional_inicial: int = Field(ge=0, le=100)
    indice_funcional_atual: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def check_sessions(self) -> "PatientFeatures":
        if self.sessoes_realizadas + self.faltas > self.sessoes_previstas:
            raise ValueError("Sessões realizadas + faltas não podem exceder as sessões previstas.")
        return self


class PatientData(PatientFeatures):
    patient_id: str = Field(pattern=r"^PAC-[0-9]{4,8}$")
    resultado: Result


REQUIRED_COLUMNS = ["patient_id", *PatientFeatures.model_fields, "resultado"]
CATEGORICAL_COLUMNS = ["patient_id", "sexo", "tipo_lesao", "resultado"]
NUMERIC_COLUMNS = [name for name in REQUIRED_COLUMNS if name not in CATEGORICAL_COLUMNS]


class RegenerateRequest(BaseModel):
    size: int = Field(default=1000, ge=1, le=10000)
    seed: int = Field(default=42, ge=0, le=2147483647)
    confirm: bool = False


class ConfirmImportRequest(BaseModel):
    token: str = Field(pattern=r"^[a-f0-9]{32}$")
