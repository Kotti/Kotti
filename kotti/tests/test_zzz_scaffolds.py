# -*- coding: utf-8 -*-

""" This module contains the tests for the scaffolds.  Each test tries to
simulate actual usage of the scaffolds as much as possible.  A clean virtualenv
is created, a package created from a scaffold and the tests of that package are
run.  Because this is potentially really time consuming the scaffolding tests
are marked with ``slow`` and are not run unless ``py.test`` is invoked with the
``--runslow`` option.

The module name starts with ``test_zzz`` to make the contained tests always the
last in a complete test run.
"""

import os

from pkg_resources import working_set
from pytest import mark

slow = mark.slow


@slow
def test_scaffold_kotti_addon(virtualenv, travis):

    # install kotti and dependencies in a fresh virtualenv
    with travis.folding_output():

        for pkgname in ('pip', 'wheel', 'setuptools', 'setuptools-git',
                        'psycopg2', 'oursql', ):
            virtualenv.run('pip install -U ' + pkgname)

        pkg = [p for p in working_set if p.project_name == 'Kotti'][0]
        d = {'python': virtualenv.python, 'src_dir': pkg.location, }

        virtualenv.run('pip install -r %(src_dir)s/requirements.txt' % d)
        if 'Kotti' in [p for p in virtualenv.installed_packages()]:
            virtualenv.run('pip uninstall -y Kotti')
        virtualenv.run('cd %(src_dir)s; %(python)s setup.py develop' % d)
        virtualenv.run('cd %(src_dir)s; %(python)s setup.py dev' % d)

    # create and develop an addon with the scaffold and run the generated tests
    with travis.folding_output():

        # print available scaffolds
        virtualenv.run('pcreate -l')

        # set some environment variables to make pcreate non interactive
        os.environ["author"] = "Kotti developers"
        os.environ["email"] = "kotti@googlegroups.com"
        os.environ["gh_user"] = "Kotti"

        virtualenv.run('pcreate -s kotti kotti_my_addon', env=os.environ)

        # develop the package
        cwd = os.path.join(virtualenv.workspace, 'kotti_my_addon')
        virtualenv.run('python setup.py develop', cwd=cwd)
        virtualenv.run('python setup.py dev', cwd=cwd)

        # run the tests
        virtualenv.run('py.test', cwd=cwd)
