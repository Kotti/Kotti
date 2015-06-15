"""This module aims to make it easier to run the Alembic migration
scripts of Kotti and Kotti add-ons by providing a uniform access.

Commands herein will typically be called by the console script
``kotti-migrate`` (see the docstring of that command below).

Kotti stores the current revision of its migration in table
``kotti_alembic_versions``.  The convention here is
``<packagename>_alembic_versions``.  You should normally not need to
worry about the name of this table, as it is created and managed
automatically through this module.  If, however, you plan to use your
own alembic.ini configuration file for your add-on or application,
keep in mind to configure a table name as described above.  The table
name can be set using Alembic's ``version_table`` option.

Kotti has start-up code that will create the database from scratch if
it doesn't exist.  This code will also call this module's function
``stamp_heads`` to set the current revision of all migrations
registered with this module to the latest.  This assumes that when we
create the database from scratch (using ``metadata.create_all``), we
don't need to run any of the past migrations.

Unfortunately, this won't help in the situation where a user adds an
add-on with migrations to the Kotti site _after_ the database was
initialized for the first time.  In this case, users of the add-on
will need to run ``kotti-migrate stamp_head
--scripts=yourpackage:alembic``, or the add-on author will have to
write equivalent code somewhere in their populate hook.

Add-on authors can register their Alembic scripts with this module by
adding their Alembic 'script directory' location to the
``kotti.alembic_dirs`` setting.  An example::

  def kotti_configure(settings):
      # ...
      settings['kotti.alembic_dirs'] += ' kotti_contactform:alembic'

``kotti-migrate`` commands 'list_all', 'upgrade_all' and
'stamp_heads' will then include the add-on.
"""
from __future__ import absolute_import

import os
import pkg_resources

from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from alembic.util import load_python_file
from zope.sqlalchemy import mark_changed

from kotti import conf_defaults
from kotti import get_settings
from kotti import DBSession
from kotti.util import command


KOTTI_SCRIPT_DIR = pkg_resources.resource_filename('kotti', 'alembic')
DEFAULT_LOCATION = 'kotti:alembic'


class ScriptDirectoryWithDefaultEnvPy(ScriptDirectory):
    @property
    def env_py_location(self):
        loc = super(ScriptDirectoryWithDefaultEnvPy, self).env_py_location
        if not os.path.exists(loc):
            loc = os.path.join(KOTTI_SCRIPT_DIR, 'env.py')
        return loc

    def run_env(self):
        dir_, filename = self.env_py_location.rsplit(os.path.sep, 1)
        load_python_file(dir_, filename)


class PackageEnvironment(object):
    def __init__(self, location):
        self.location = location
        self.config = self._make_config(location)
        self.script_dir = self._make_script_dir(self.config)

    @property
    def pkg_name(self):
        return self.location.split(':')[0]

    @property
    def version_table(self):
        return '{0}_alembic_version'.format(self.pkg_name)

    def run_env(self, fn, **kw):
        with EnvironmentContext(self.config, self.script_dir, fn=fn,
                                version_table=self.version_table, **kw):
            self.script_dir.run_env()

    def _make_config(self, location):
        cfg = Config()
        cfg.set_main_option("script_location", location)
        cfg.set_main_option("sqlalchemy.url", get_settings()['sqlalchemy.url'])
        return cfg

    def _make_script_dir(self, alembic_cfg):
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        script_dir.__class__ = ScriptDirectoryWithDefaultEnvPy  # O_o
        return script_dir


def get_locations():
    conf_str = get_settings()['kotti.alembic_dirs']
    return [l.strip() for l in conf_str.split() if l.strip()]


def stamp_head(location=DEFAULT_LOCATION, revision=None):

    env = PackageEnvironment(location)

    def do_stamp(rev, context, revision=revision):

        if revision is None:
            revision = context.script.get_current_head()
        elif revision == 'None':
            revision = None

        context.stamp(env.script_dir, revision)

        mark_changed(DBSession())
        return []

    env.run_env(do_stamp)


def stamp_heads():
    for location in get_locations():
        stamp_head(location)


def upgrade(location=DEFAULT_LOCATION):
    # We don't want to fire any kind of events during a migration,
    # because "migrations are a low-level thing".
    from kotti import events
    events.clear()

    pkg_env = PackageEnvironment(location)

    revision = pkg_env.script_dir.get_current_head()
    print(u'Upgrading {0}:'.format(pkg_env.location))

    def upgrade(heads, context):
        # alembic supports multiple heads, we don't.
        # initial revision is () in alembic >= 0.7
        rev = heads[0] if heads else None

        if rev == revision:
            print(u'  - already up to date.')
            return []

        print(u'  - upgrading from {0} to {1}...'.format(rev, revision))

        return context.script._upgrade_revs(revision, rev)

    pkg_env.run_env(
        upgrade,
        starting_rev=None,
        destination_rev=revision,
        )
    print


def upgrade_all():
    for location in get_locations():
        upgrade(location)


def list_all():
    pkg_envs = [PackageEnvironment(l) for l in get_locations()]
    for pkg_env in pkg_envs:
        print(u'{0}:'.format(pkg_env.pkg_name))

        for script in pkg_env.script_dir.walk_revisions():
            print(u"  - {0} -> {1}: {2}".format(
                script.down_revision,
                script.revision,
                script.doc,
                ))

        def current_revision(rev, context):
            rev = rev[0] if rev else None
            print(u"  - current revision: {0}".format(rev))
            return []
        pkg_env.run_env(current_revision)
        print


def kotti_migrate_command():
    __doc__ = """Migrate Kotti and Kotti add-ons.

    Usage:
      kotti-migrate <config_uri> list_all
      kotti-migrate <config_uri> upgrade [--scripts=<location>]
      kotti-migrate <config_uri> upgrade_all
      kotti-migrate <config_uri> stamp_head [--scripts=<location>] [--rev=<rev>]

    o 'list_all' prints a list of all available migrations of Kotti
      and registered add-ons.

    o 'upgrade' will run Kotti's upgrades to upgrade the database to
    the latest version.

      Use '--scripts=kotti_myaddon:alembic' to run the upgrades of the
      'kotti_myaddon' package instead.

    o 'upgrade_all' will run all upgrades of all packages registered
      with Kotti.

    o 'stamp_head' allows you to manually set the stamped version to
      the latest version inside the 'kotti_alembic_version' table,
      that is, without actually running any migrations.

      You may use this command for a different package by using the
      '--scripts' option.

    Options:
      -h --help     Show this screen.
    """
    # We need to turn off populators and root_factory when we run
    # migrations, because they would access the database, which may
    # not be possible prior to the migration.
    #
    # Unfortunately, we're not able to just set the 'kotti.populators'
    # setting to an empty list.  Since add-ons might add to this list
    # again later, when we call 'bootstrap' (and thus their
    # 'includeme' function).
    save_conf_defaults = conf_defaults.copy()

    os.environ['KOTTI_DISABLE_POPULATORS'] = '1'
    conf_defaults['kotti.root_factory'] = [lambda req: None]

    def callback(arguments):
        args = ()
        args_with_location = (arguments['--scripts'] or DEFAULT_LOCATION,)
        if arguments['list_all']:
            func = list_all
        elif arguments['upgrade']:
            func = upgrade
            args = args_with_location
        elif arguments['upgrade_all']:
            func = upgrade_all
        elif arguments['stamp_head']:
            func = stamp_head
            args = args_with_location + (arguments['--rev'],)
        func(*args)

    try:
        return command(callback, __doc__)
    finally:
        conf_defaults.clear()
        conf_defaults.update(save_conf_defaults)
        del os.environ['KOTTI_DISABLE_POPULATORS']
