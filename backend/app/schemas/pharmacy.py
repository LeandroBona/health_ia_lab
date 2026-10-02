"""Single source of truth for Pharmacy dataset and prediction validation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ADHERENCE_CLASSES = ["alta", "moderada", "baixa"]
ADHERENCE_FEATURES = [
    "idade", "quantidade_medicamentos", "doses_diarias", "tempo_tratamento_dias",
    "esquecimentos_30_dias", "retiradas_atrasadas", "consultas_acompanhamento",
    "usa_organizador", "recebe_lembretes", "complexidade_rotina",
]
ADHERENCE_COLUMNS = ["patient_id", *ADHERENCE_FEATURES, "adesao_percentual", "categoria_adesao"]
DEMAND_COLUMNS = [
    "medication_id", "month", "year", "period", "stock_initial", "quantity_received",
    "quantity_used", "stock_final", "seasonality_index", "trend_index", "promotion_event", "demand",
]


class AdherenceFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    idade: int = Field(ge=18, le=85)
    quantidade_medicamentos: int = Field(ge=1, le=10)
    doses_diarias: int = Field(ge=1, le=6)
    tempo_tratamento_dias: int = Field(ge=1, le=1460)
    esquecimentos_30_dias: int = Field(ge=0, le=30)
    retiradas_atrasadas: int = Field(ge=0, le=12)
    consultas_acompanhamento: int = Field(ge=0, le=24)
    usa_organizador: bool
    recebe_lembretes: bool
    complexidade_rotina: int = Field(ge=1, le=5)


class AdherenceRow(AdherenceFeatures):
    patient_id: str = Field(pattern=r"^FAR-[0-9]{4,}$")
    adesao_percentual: float = Field(ge=0, le=100)
    categoria_adesao: Literal["alta", "moderada", "baixa"]


class DemandRow(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    medication_id: str = Field(pattern=r"^MED-[0-9]{3,}$")
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2020, le=2100)
    period: str = Field(pattern=r"^20[0-9]{2}-(0[1-9]|1[0-2])$")
    stock_initial: int = Field(ge=0, le=100000)
    quantity_received: int = Field(ge=0, le=100000)
    quantity_used: int = Field(ge=0, le=100000)
    stock_final: int = Field(ge=0, le=100000)
    seasonality_index: float = Field(ge=0.2, le=2.0)
    trend_index: float = Field(ge=0, le=10000)
    promotion_event: bool
    demand: int = Field(ge=0, le=100000)

    @model_validator(mode="after")
    def validate_relationships(self):
        if self.period != f"{self.year:04d}-{self.month:02d}":
            raise ValueError("period deve corresponder a month e year")
        if self.stock_initial + self.quantity_received - self.quantity_used != self.stock_final:
            raise ValueError("stock_final deve fechar o balanço de estoque")
        if self.quantity_used > self.demand:
            raise ValueError("quantity_used não pode superar demand")
        return self


class ConfirmImport(BaseModel):
    token: str = Field(pattern=r"^[a-f0-9]{32}$")
