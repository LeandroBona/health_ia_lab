"""Apply additive Alembic revisions while preserving pre-migration SQLite data."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

BASELINE_REVISION = "c6c00b0c2c34"
BACKEND_DIR = Path(__file__).resolve().parents[2]


def run_migrations(engine: Engine) -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        tables = set(inspect(connection).get_table_names())
        if tables and "alembic_version" not in tables:
            # Parts 1–10 used Base.metadata.create_all. Their schema is the baseline.
            command.stamp(config, BASELINE_REVISION)
        command.upgrade(config, "head")
