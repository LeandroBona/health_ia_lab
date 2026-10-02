from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class VeterinaryDataset(Base):
    __tablename__ = "veterinary_datasets"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String(40))


class VeterinaryAnimal(Base):
    __tablename__ = "veterinary_animals"
    animal_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("veterinary_datasets.id"), index=True)
    especie: Mapped[str] = mapped_column(String(30))
    idade_anos: Mapped[float] = mapped_column(Float)
    peso_kg: Mapped[float] = mapped_column(Float)
    sexo: Mapped[str] = mapped_column(String(12))
    procedimento: Mapped[str] = mapped_column(String(60))
    dias_pos_procedimento: Mapped[int] = mapped_column(Integer)
    temperatura: Mapped[float] = mapped_column(Float)
    frequencia_cardiaca: Mapped[float] = mapped_column(Float)
    atividade_percentual: Mapped[float] = mapped_column(Float)
    alimentacao_percentual: Mapped[float] = mapped_column(Float)
    hidratacao_percentual: Mapped[float] = mapped_column(Float)
    medicacao_administrada_percentual: Mapped[float] = mapped_column(Float)
    retornos_realizados: Mapped[int] = mapped_column(Integer)
    retornos_previstos: Mapped[int] = mapped_column(Integer)
    alteracoes_reportadas: Mapped[int] = mapped_column(Integer)
    indice_recuperacao: Mapped[float] = mapped_column(Float)
    evolucao: Mapped[str] = mapped_column(String(30), index=True)
    followups: Mapped[list["VeterinaryFollowUp"]] = relationship(back_populates="animal")


class VeterinaryFollowUp(Base):
    __tablename__ = "veterinary_followups"
    followup_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    animal_id: Mapped[str] = mapped_column(ForeignKey("veterinary_animals.animal_id"), index=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("veterinary_datasets.id"), index=True)
    timestamp: Mapped[str] = mapped_column(String(40), index=True)
    temperatura: Mapped[float] = mapped_column(Float)
    frequencia_cardiaca: Mapped[float] = mapped_column(Float)
    atividade_percentual: Mapped[float] = mapped_column(Float)
    alimentacao_percentual: Mapped[float] = mapped_column(Float)
    hidratacao_percentual: Mapped[float] = mapped_column(Float)
    alteracoes_reportadas: Mapped[int] = mapped_column(Integer)
    classification: Mapped[str | None] = mapped_column(String(10), nullable=True)
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    animal: Mapped[VeterinaryAnimal] = relationship(back_populates="followups")


class VeterinaryImportPreview(Base):
    __tablename__ = "veterinary_import_previews"
    token: Mapped[str] = mapped_column(String(32), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    filename: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[float] = mapped_column(Float)
    payload: Mapped[str] = mapped_column(Text)
