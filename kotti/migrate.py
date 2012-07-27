import os
import pkg_resources

from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from alembic.util import load_python_file
from docopt import docopt
from pyramid.paster import bootstrap

from kotti import conf_defaults
from kotti import get_settings

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
        self.config = self.make_config(location)
        self.script_dir = self.make_script_dir(self.config)

    @property
    def pkg_name(self):
        return self.location.split(':')[0]

    @property
    def version_table(self):
        return '{0}_alembic_version'.format(self.pkg_name)

    def run_env(self, fn, **kw):
        with EnvironmentContext(
            self.config,
            self.script_dir,
            fn=fn,
            version_table=self.version_table,
            **kw
            ):
            self.script_dir.run_env()

    def make_config(self, location):
        cfg = Config()
        cfg.set_main_option("script_location", location)
        cfg.set_main_option("sqlalchemy.url", get_settings()['sqlalchemy.url'])
        return cfg

    def make_script_dir(self, alembic_cfg):
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        script_dir.__class__ = ScriptDirectoryWithDefaultEnvPy  # O_o
        return script_dir


def get_locations():
    conf_str = get_settings()['kotti.alembic_script_locations']
    return [l.strip() for l in conf_str.split() if l.strip()]


def stamp_head(location=DEFAULT_LOCATION, revision=None):
    pkg_env = PackageEnvironment(location)

    def do_stamp(rev, context, revision=revision):
        current = context._current_rev()
        if revision is None:
            revision = pkg_env.script_dir.get_current_head()
        elif revision == 'None':
            revision = None
        context._update_current_rev(current, revision)
        return []

    pkg_env.run_env(do_stamp)


def upgrade(location=DEFAULT_LOCATION):
    pkg_env = PackageEnvironment(location)

    revision = pkg_env.script_dir.get_current_head()
    print(u'Upgrading {0}:'.format(pkg_env.location))

    def upgrade(rev, context):
        if rev == revision:
            print(u'  - already up to date.')
            return []
        print(u'  - upgrading from {0} to {1}...'.format(
            rev, revision))
        return pkg_env.script_dir._upgrade_revs(revision, rev)

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
            print(u"  - current revision: {0}".format(rev))
            return []
        pkg_env.run_env(current_revision)
        print


def main():
    __doc__ = """Migrate Kotti and Kotti add-ons.

    Usage:
      kotti-migrate <config_uri> list_all
      kotti-migrate <config_uri> upgrade [--location=<location>]
      kotti-migrate <config_uri> upgrade_all
      kotti-migrate <config_uri> stamp_head [--location=<location>] [--rev=<rev>]

    Options:
      -h --help     Show this screen.
    """
    # We need to turn these off, because they would access the
    # database, which may not be possible prior to the migration:
    os.environ['KOTTI_DISABLE_POPULATORS'] = '1'
    conf_defaults['kotti.root_factory'] = [lambda req: None]

    arguments = docopt(__doc__)
    pyramid_env = bootstrap(arguments['<config_uri>'])

    args = ()
    args_with_location = (arguments['--location'] or DEFAULT_LOCATION,)
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

    try:
        func(*args)
    finally:
        pyramid_env['closer']()
