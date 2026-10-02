"""Minimal educational audit trail: no raw inputs, prompts, images, or frames."""
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    __table_args__ = (
        Index("ix_analysis_history_module_created", "module", "created_at"),
        Index("ix_analysis_history_type_created", "analysis_type", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    module: Mapped[str] = mapped_column(String(30), index=True)
    analysis_type: Mapped[str] = mapped_column(String(45), index=True)
    model_name: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    record_reference: Mapped[str | None] = mapped_column(String(60), nullable=True)
    result_summary: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[str] = mapped_column(String(40), index=True)
    source_history_id: Mapped[str | None] = mapped_column(ForeignKey("analysis_history.id"), nullable=True)
