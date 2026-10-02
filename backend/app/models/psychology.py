from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PsychologyDataset(Base):
    __tablename__ = "psychology_datasets"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String(40))


class PsychologyRecord(Base):
    __tablename__ = "psychology_records"
    record_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("psychology_datasets.id"), index=True)
    idade_faixa: Mapped[str | None] = mapped_column(String(10), nullable=True)
    contexto: Mapped[str] = mapped_column(String(40), index=True)
    texto: Mapped[str] = mapped_column(Text)
    tema_principal: Mapped[str] = mapped_column(String(30), index=True)
    tema_secundario: Mapped[str | None] = mapped_column(String(30), nullable=True)
    data_sintetica: Mapped[str | None] = mapped_column(String(20), nullable=True)


class PsychologyImportPreview(Base):
    __tablename__ = "psychology_import_previews"
    token: Mapped[str] = mapped_column(String(32), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[float] = mapped_column(Float)
    payload: Mapped[str] = mapped_column(Text)
