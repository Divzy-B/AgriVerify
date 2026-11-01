from alembic import context

from app.db import Base
from app.core.config import get_settings
from app import models  # noqa: F401

target_metadata = Base.metadata

# Alembic normally reads a local SQLite URL from alembic.ini. Use the same
# environment-backed configuration as the application so migrations target
# Cloud SQL in production and SQLite only when explicitly configured locally.
config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))

def run_migrations_offline():
    context.configure(url=context.config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction(): context.run_migrations()

def run_migrations_online():
    from sqlalchemy import engine_from_config, pool
    connectable = engine_from_config(context.config.get_section(context.config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction(): context.run_migrations()

if __name__ == "__main__":
    run_migrations_online()

