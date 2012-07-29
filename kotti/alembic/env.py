from alembic import context
from sqlalchemy import engine_from_config, pool

from kotti import metadata as target_metadata


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


try:  # Alembic's "if __name__ == '__main__'"
    offline_mode = context.is_offline_mode()
except AttributeError:
    pass
else:
    if offline_mode:  # pragma: no cover
        raise ValueError(
            "\nNo support for Alembic's offline mode at this point."
            "\nYou may want to write your own env.py script to use "
            "\n'offline mode'."
            )
    run_migrations_online()
