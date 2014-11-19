# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
from sys import stdout
from tempfile import mkdtemp

from pytest import fixture
from pytest import mark

slow = mark.slow


@fixture
def virtualenv(request):
    """ Create a virtualenv and ``chdir`` into it.  Remove it and ``chdir``
    into the previous working directory again when the test has been run.
    """

    import virtualenv
    from virtualenv import Logger

    # create a temp directory
    cwd = os.getcwd()
    virtualenv_directory = mkdtemp()
    os.chdir(virtualenv_directory)

    # install a virtualenv
    logger = Logger([(Logger.level_for_integer(2), stdout)])
    virtualenv.logger = logger
    virtualenv.create_environment(
        virtualenv_directory,
        site_packages=False,
        clear=False,
        unzip_setuptools=True)

    # install requirements.txt into the virtualenv
    subprocess.check_call([
        os.path.join(virtualenv_directory, 'bin', 'pip'),
        'install', '-r',
        os.path.join(cwd, 'requirements.txt')])

    # install Kotti into the virtualenv
    subprocess.check_call([
        os.path.join(virtualenv_directory, 'bin', 'python'),
        os.path.join(cwd, 'setup.py'),
        'install'])

    def delete_virtualenv():
        shutil.rmtree(virtualenv_directory)
        os.chdir(cwd)

    request.addfinalizer(delete_virtualenv)


@slow
def test_scaffold_kotti_addon(virtualenv):

    import pdb; pdb.set_trace()
    pass
