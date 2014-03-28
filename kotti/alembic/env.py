from alembic import context
import traceback
import transaction
from zope.sqlalchemy import mark_changed

from kotti import DBSession
from kotti import metadata


def run_migrations_online():
    if DBSession.bind is None:
        raise ValueError(
            "\nYou must run Kotti's migration using the 'kotti-migrate' script"
            "\nand not through 'alembic' directly."
            )

    transaction.begin()
    connection = DBSession.connection()

    context.configure(
        connection=connection,
        target_metadata=metadata,
        )

    try:
        context.run_migrations()
        mark_changed(DBSession())
    except:
        traceback.print_exc()
        transaction.abort()
    else:
        transaction.commit()
    finally:
        # connection.close()
        pass


try:  # Alembic's "if __name__ == '__main__'"
    offline_mode = context.is_offline_mode()
except (AttributeError, NameError):
    pass
else:
    if offline_mode:  # pragma: no cover
        raise ValueError(
            "\nNo support for Alembic's offline mode at this point."
            "\nYou may want to write your own env.py script to use "
            "\n'offline mode'."
            )
    run_migrations_online()
