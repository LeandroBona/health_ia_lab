from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class shared by future patient, dataset and analysis models."""

