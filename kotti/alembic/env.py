from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool

from kotti import metadata as target_metadata


def run_migrations_offline():
    config = context.config
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    config = context.config

    engine = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
        )

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()


try:
    offline_mode = context.is_offline_mode()
except AttributeError:
    pass
else:
    if offline_mode:
        run_migrations_offline()
    else:
        run_migrations_online()
