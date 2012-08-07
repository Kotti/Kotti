from alembic import context
import transaction

from kotti import DBSession
from kotti import metadata


def run_migrations_online():
    if DBSession.bind is not None:
        transaction.begin()
        connection = DBSession.connection()
    else:
        raise ValueError(
            "\nYou must run Kotti's migration using the 'kotti-migrate' script"
            "\nthrough 'alembic' directly."
            )

    context.configure(
        connection=connection,
        target_metadata=metadata,
        )

    try:
        context.run_migrations()
        transaction.commit()
    except:
        transaction.abort()
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
