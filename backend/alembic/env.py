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

# Alembic imports this file rather than executing it as ``__main__``.  Invoke
# the appropriate runner at import time, as Alembic's generated env.py does;
# otherwise ``alembic upgrade head`` exits successfully without applying a
# migration.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

