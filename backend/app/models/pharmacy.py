from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PharmacyDataset(Base):
    __tablename__ = "pharmacy_datasets"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String(40))


class PharmacyAdherencePatient(Base):
    __tablename__ = "pharmacy_adherence_patients"
    patient_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("pharmacy_datasets.id"), index=True)
    idade: Mapped[int] = mapped_column(Integer)
    quantidade_medicamentos: Mapped[int] = mapped_column(Integer)
    doses_diarias: Mapped[int] = mapped_column(Integer)
    tempo_tratamento_dias: Mapped[int] = mapped_column(Integer)
    esquecimentos_30_dias: Mapped[int] = mapped_column(Integer)
    retiradas_atrasadas: Mapped[int] = mapped_column(Integer)
    consultas_acompanhamento: Mapped[int] = mapped_column(Integer)
    usa_organizador: Mapped[bool] = mapped_column(Boolean)
    recebe_lembretes: Mapped[bool] = mapped_column(Boolean)
    complexidade_rotina: Mapped[int] = mapped_column(Integer)
    adesao_percentual: Mapped[float] = mapped_column(Float)
    categoria_adesao: Mapped[str] = mapped_column(String(12), index=True)


class PharmacyDemandRecord(Base):
    __tablename__ = "pharmacy_demand_records"
    __table_args__ = (UniqueConstraint("medication_id", "period", name="uq_pharmacy_medication_period"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("pharmacy_datasets.id"), index=True)
    medication_id: Mapped[str] = mapped_column(String(20), index=True)
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    period: Mapped[str] = mapped_column(String(7), index=True)
    stock_initial: Mapped[int] = mapped_column(Integer)
    quantity_received: Mapped[int] = mapped_column(Integer)
    quantity_used: Mapped[int] = mapped_column(Integer)
    stock_final: Mapped[int] = mapped_column(Integer)
    seasonality_index: Mapped[float] = mapped_column(Float)
    trend_index: Mapped[float] = mapped_column(Float)
    promotion_event: Mapped[bool] = mapped_column(Boolean)
    demand: Mapped[int] = mapped_column(Integer)


class PharmacyImportPreview(Base):
    __tablename__ = "pharmacy_import_previews"
    token: Mapped[str] = mapped_column(String(32), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    filename: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[float] = mapped_column(Float)
    payload: Mapped[str] = mapped_column(Text)
