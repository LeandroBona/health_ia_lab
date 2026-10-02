import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.data_generators.psychology import AGE_RANGES, COLUMNS, CONTEXTS, THEMES

REQUIRED_COLUMNS = ["record_id", "texto", "tema_principal", "contexto"]
OPTIONAL_COLUMNS = [column for column in COLUMNS if column not in REQUIRED_COLUMNS]
CONTACT_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}|\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}\b", re.I)


class TextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Digite um texto fictício não vazio.")
        return value


class RecordRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_id: str = Field(pattern=r"^PSI-[0-9]{4,}$")
    idade_faixa: Literal[tuple(AGE_RANGES)] | None = None
    contexto: Literal[tuple(CONTEXTS)]
    texto: str = Field(min_length=10, max_length=2000)
    tema_principal: Literal[tuple(THEMES)]
    tema_secundario: Literal[tuple(THEMES)] | None = None
    data_sintetica: str | None = None

    @field_validator("texto")
    @classmethod
    def synthetic_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Texto vazio não é permitido.")
        if CONTACT_RE.search(value):
            raise ValueError("O texto não pode incluir email, telefone ou documento pessoal.")
        return value

    @field_validator("data_sintetica")
    @classmethod
    def valid_date(cls, value: str | None) -> str | None:
        if value:
            date.fromisoformat(value)
        return value

    @model_validator(mode="after")
    def different_topics(self):
        if self.tema_secundario == self.tema_principal:
            raise ValueError("Os dois temas devem ser diferentes.")
        return self


class ConfirmImport(BaseModel):
    token: str = Field(pattern=r"^[a-f0-9]{32}$")
