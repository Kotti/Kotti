# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import sys
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

    # install a virtualenv
    logger = Logger([(Logger.level_for_integer(2), sys.stdout)])
    virtualenv.logger = logger
    virtualenv.create_environment(
	virtualenv_directory,
	site_packages=True,
	clear=False,
	unzip_setuptools=True)

    # chdir into the virtualenv directory
    os.chdir(virtualenv_directory)

    # install requirements.txt into the virtualenv
    subprocess.check_call([
	os.path.join('bin', 'pip'),
	'install', '-r',
	os.path.join(cwd, 'requirements.txt')])

    # also install psycopg2 and oursql
    subprocess.check_call([
	os.path.join('bin', 'pip'),
	'install', 'psycopg2', 'oursql'])

    # setuptools-git is required to be able to call setup.py install
    # sucessfully.
    subprocess.check_call([
	os.path.join('bin', 'pip'),
	'install', 'setuptools-git'])

    shutil.copytree(cwd, os.path.join(virtualenv_directory, 'kotti'))

    # install Kotti into the virtualenv
    os.chdir('kotti')
    subprocess.check_call([
	os.path.join('..', 'bin', 'python'), 'setup.py', 'develop'])
    os.chdir('..')

    def delete_virtualenv():
	shutil.rmtree(virtualenv_directory)
	os.chdir(cwd)

    request.addfinalizer(delete_virtualenv)


@slow
def test_scaffold_kotti_addon(virtualenv):

    # print available scaffolds
    subprocess.check_call([os.path.join('bin', 'pcreate'), '-l'])

    # set some environment variables to make pcreate non interactive
    os.environ["author"] = "Kotti developers"
    os.environ["email"] = "kotti@googlegroups.com"
    os.environ["gh_user"] = "Kotti"

    # create a project from the scaffold
    subprocess.check_call([
	os.path.join('bin', 'pcreate'),
	'-s', 'kotti_addon', 'kotti_my_addon'])

    # develop the package
    os.chdir('kotti_my_addon')
    subprocess.check_call([
	os.path.join('..', 'bin', 'python'),
	'setup.py', 'develop'])
    subprocess.check_call([
	os.path.join('..', 'bin', 'python'),
	'setup.py', 'dev'])

    # run the tests
    subprocess.check_call([
	os.path.join('..', 'bin', 'py.test')])

    pass
