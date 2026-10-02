from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PhysiotherapyDataset(Base):
    __tablename__ = "physiotherapy_datasets"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String(40))


class PhysiotherapyPatient(Base):
    __tablename__ = "physiotherapy_patients"
    __table_args__ = (
        CheckConstraint("idade BETWEEN 18 AND 85"),
        CheckConstraint("sessoes_realizadas >= 0 AND faltas >= 0 AND sessoes_realizadas + faltas <= sessoes_previstas"),
    )

    patient_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("physiotherapy_datasets.id"), index=True)
    idade: Mapped[int] = mapped_column(Integer)
    sexo: Mapped[str] = mapped_column(String(10), index=True)
    tipo_lesao: Mapped[str] = mapped_column(String(30), index=True)
    tempo_lesao_dias: Mapped[int] = mapped_column(Integer)
    dor_inicial: Mapped[int] = mapped_column(Integer)
    dor_atual: Mapped[int] = mapped_column(Integer)
    mobilidade_inicial: Mapped[int] = mapped_column(Integer)
    mobilidade_atual: Mapped[int] = mapped_column(Integer)
    forca_muscular: Mapped[int] = mapped_column(Integer)
    sessoes_previstas: Mapped[int] = mapped_column(Integer)
    sessoes_realizadas: Mapped[int] = mapped_column(Integer)
    faltas: Mapped[int] = mapped_column(Integer)
    adesao_exercicios: Mapped[int] = mapped_column(Integer)
    comorbidades: Mapped[int] = mapped_column(Integer)
    indice_funcional_inicial: Mapped[int] = mapped_column(Integer)
    indice_funcional_atual: Mapped[int] = mapped_column(Integer)
    resultado: Mapped[str] = mapped_column(String(30), index=True)


class ImportPreview(Base):
    __tablename__ = "physiotherapy_import_previews"

    token: Mapped[str] = mapped_column(String(32), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[float]
    payload: Mapped[str] = mapped_column(Text)
