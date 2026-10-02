"""Alembic environment for the existing HealthAI Lab SQLAlchemy schema."""
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.database.session import DATABASE_URL
from app.models.base import Base
import app.models.physiotherapy  # noqa: F401
import app.models.nursing  # noqa: F401
import app.models.pharmacy  # noqa: F401
import app.models.veterinary  # noqa: F401
import app.models.psychology  # noqa: F401
import app.models.analysis_history  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)
target_metadata = Base.metadata


def include_object(object_, name, type_, reflected, compare_to):
    return not (os.getenv("HEALTHAI_BASELINE") == "1" and name == "analysis_history")


def run_migrations_online():
    connection = config.attributes.get("connection")
    if connection is None:
        engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object, compare_type=True)
            with context.begin_transaction():
                context.run_migrations()
        engine.dispose()
    else:
        context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_offline():
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, include_object=include_object, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
