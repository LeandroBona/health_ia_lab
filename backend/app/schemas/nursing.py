from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

FEATURES = [
    "frequencia_cardiaca", "frequencia_respiratoria", "temperatura",
    "pressao_sistolica", "pressao_diastolica", "saturacao", "nivel_dor",
]
REQUIRED_COLUMNS = ["measurement_id", "patient_id", "timestamp", "idade", *FEATURES, "estado"]
RANGES = {
    "frequencia_cardiaca": (30, 220), "frequencia_respiratoria": (5, 60),
    "temperatura": (30, 45), "pressao_sistolica": (50, 250),
    "pressao_diastolica": (25, 150), "saturacao": (50, 100), "nivel_dor": (0, 10),
}


class Signals(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    frequencia_cardiaca: float = Field(ge=30, le=220)
    frequencia_respiratoria: float = Field(ge=5, le=60)
    temperatura: float = Field(ge=30, le=45)
    pressao_sistolica: float = Field(ge=50, le=250)
    pressao_diastolica: float = Field(ge=25, le=150)
    saturacao: float = Field(ge=50, le=100)
    nivel_dor: float = Field(ge=0, le=10)

    @model_validator(mode="after")
    def pressure_relation(self):
        if self.pressao_diastolica >= self.pressao_sistolica:
            raise ValueError("Pressão diastólica deve ser menor que pressão sistólica.")
        return self


class MeasurementRow(Signals):
    measurement_id: str = Field(pattern=r"^MED-[0-9]{6,}$")
    patient_id: str = Field(pattern=r"^ENF-[0-9]{4,}$")
    timestamp: datetime
    idade: int = Field(ge=18, le=90)
    estado: Literal["padrao", "alterado"]

    @model_validator(mode="after")
    def timezone_required(self):
        if self.timestamp.tzinfo is None:
            raise ValueError("Timestamp deve incluir fuso horário.")
        return self


class ConfirmImport(BaseModel):
    token: str = Field(pattern=r"^[a-f0-9]{32}$")
