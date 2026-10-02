from sqlalchemy import ForeignKey, Integer, String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NursingDataset(Base):
    __tablename__ = "nursing_datasets"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    patient_count: Mapped[int] = mapped_column(Integer)
    measurement_count: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String(40))


class NursingPatient(Base):
    __tablename__ = "nursing_patients"
    patient_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    idade: Mapped[int] = mapped_column(Integer)
    measurements: Mapped[list["NursingMeasurement"]] = relationship(back_populates="patient")


class NursingMeasurement(Base):
    __tablename__ = "nursing_measurements"
    measurement_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("nursing_patients.patient_id"), index=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("nursing_datasets.id"), index=True)
    timestamp: Mapped[str] = mapped_column(String(40), index=True)
    idade: Mapped[int] = mapped_column(Integer)
    frequencia_cardiaca: Mapped[float] = mapped_column(Float)
    frequencia_respiratoria: Mapped[float] = mapped_column(Float)
    temperatura: Mapped[float] = mapped_column(Float)
    pressao_sistolica: Mapped[float] = mapped_column(Float)
    pressao_diastolica: Mapped[float] = mapped_column(Float)
    saturacao: Mapped[float] = mapped_column(Float)
    nivel_dor: Mapped[float] = mapped_column(Float)
    estado: Mapped[str] = mapped_column(String(10))
    classification: Mapped[str | None] = mapped_column(String(12), nullable=True, index=True)
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    analyzed_model_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    patient: Mapped[NursingPatient] = relationship(back_populates="measurements")


class NursingImportPreview(Base):
    __tablename__ = "nursing_import_previews"
    token: Mapped[str] = mapped_column(String(32), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[float] = mapped_column(Float)
    payload: Mapped[str] = mapped_column(Text)


class NursingAnalysisRun(Base):
    __tablename__ = "nursing_analysis_runs"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    analyzed_at: Mapped[str] = mapped_column(String(40))
    model_version: Mapped[str] = mapped_column(String(20))
    measurement_count: Mapped[int] = mapped_column(Integer)
    anomaly_count: Mapped[int] = mapped_column(Integer)
