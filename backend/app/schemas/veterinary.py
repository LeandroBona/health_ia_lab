from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.data_generators.veterinary import ANIMAL_COLUMNS, CLASSES, PROCEDURES, SPECIES
from app.data_generators.veterinary_followup import FOLLOWUP_COLUMNS

DATASET_COLUMNS = {"animals": ANIMAL_COLUMNS, "followups": FOLLOWUP_COLUMNS}


class AnimalFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")
    especie: Literal[tuple(SPECIES)]
    idade_anos: float = Field(ge=.2, le=25)
    peso_kg: float = Field(gt=0, le=850)
    sexo: Literal["Fêmea", "Macho"]
    procedimento: Literal[tuple(PROCEDURES)]
    dias_pos_procedimento: int = Field(ge=0, le=365)
    temperatura: float = Field(ge=35, le=41)
    frequencia_cardiaca: float = Field(ge=25, le=230)
    atividade_percentual: float = Field(ge=0, le=100)
    alimentacao_percentual: float = Field(ge=0, le=100)
    hidratacao_percentual: float = Field(ge=0, le=100)
    medicacao_administrada_percentual: float = Field(ge=0, le=100)
    retornos_realizados: int = Field(ge=0, le=20)
    retornos_previstos: int = Field(ge=0, le=20)
    alteracoes_reportadas: int = Field(ge=0, le=10)
    indice_recuperacao: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def check_returns(self):
        if self.retornos_realizados > self.retornos_previstos:
            raise ValueError("retornos_realizados deve ser menor ou igual a retornos_previstos")
        return self


class AnimalRow(AnimalFeatures):
    animal_id: str = Field(pattern=r"^VET-[0-9]{4,}$")
    evolucao: Literal[tuple(CLASSES)]


class FollowUpFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")
    temperatura: float = Field(ge=35, le=41)
    frequencia_cardiaca: float = Field(ge=25, le=230)
    atividade_percentual: float = Field(ge=0, le=100)
    alimentacao_percentual: float = Field(ge=0, le=100)
    hidratacao_percentual: float = Field(ge=0, le=100)
    alteracoes_reportadas: int = Field(ge=0, le=10)


class FollowUpRow(FollowUpFeatures):
    followup_id: str = Field(pattern=r"^FUP-[0-9]{6,}$")
    animal_id: str = Field(pattern=r"^VET-[0-9]{4,}$")
    timestamp: str


class ConfirmImport(BaseModel):
    token: str = Field(pattern=r"^[a-f0-9]{32}$")
