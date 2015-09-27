import os
import sys

from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    AUTHORS = open(os.path.join(here, 'AUTHORS.txt')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = AUTHORS = CHANGES = ''

install_requires = [
    'Babel',
    'Chameleon>=2.7.4',  # Fixes error when raising HTTPFound
    'Pillow',  # dependency of plone.scale
    'alembic>=0.8.0',
    'bleach',
    'bleach-whitelist',
    'colander>=0.9.3',
    'deform>=2.0a1',  # >=2.0a1 to support Bootstrap 2
    'docopt',
    'filedepot',
    'formencode',
    'html2text',
    'js.angular',
    'js.bootstrap>=3.0.0',
    'js.deform>=2.0a2-2',
    'js.fineuploader',
    'js.html5shiv',
    'js.jquery',
    'js.jquery_form',
    'js.jquery_tablednd',
    'js.jquery_timepicker_addon',
    'js.jqueryui>=1.8.24',
    'js.jqueryui_tagit',
    'lingua>=1.3',
    'plone.scale',  # needed for image resizing capabilities
    'py_bcrypt',
    'pyramid>=1.5',  # needed for ``request.has_permission``
    'pyramid_beaker',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'pyramid_deform>=0.2a3',  # language and template path config includeme
    'pyramid_mailer',
    'pyramid_tm',
    'pyramid_zcml',
    'repoze.lru',
    'repoze.workflow',
    'sqlalchemy>=1.0.0',
    'sqlalchemy-utils',
    'transaction>=1.1.0',
    'unidecode',
    'usersettings',
    'waitress',
    'zope.deprecation',
    'zope.sqlalchemy',
    ]

tests_require = [
    'WebTest',
    'mock',
    'pyquery',
    'pytest>=2.4.2',
    'pytest-cov',
    'pytest-pep8!=1.0.3',
    'pytest-xdist',
    'virtualenv',  # needed for scaffolding tests
    'wsgi_intercept==0.5.1',
    'zope.testbrowser',
    ]

development_requires = [
    'minify',
    ]

docs_require = [
    'Sphinx',
    'docutils',
    'repoze.sphinx.autointerface',
    'sphinx_rtd_theme',
    ]

if sys.version_info[:3] < (2, 7, 0):
    install_requires.append('ordereddict')

setup(name='Kotti',
      version='1.2.0',
      description="A high-level, Pythonic web application framework based on Pyramid and SQLAlchemy.  It includes an extensible Content Management System called the Kotti CMS.",  # noqa
      long_description='\n\n'.join([README, AUTHORS, CHANGES]),
      classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: Repoze Public License",
      ],
      author='Kotti developers',
      author_email='kotti@googlegroups.com',
      url='http://kotti.pylonsproject.org/',
      keywords='kotti web cms wcms pylons pyramid sqlalchemy bootstrap',
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      dependency_links=[],
      entry_points="""\
      [paste.app_factory]
      main = kotti:main

      [fanstatic.libraries]
      kotti = kotti.fanstatic:lib_kotti

      [console_scripts]
      kotti-migrate = kotti.migrate:kotti_migrate_command
      kotti-reset-workflow = kotti.workflow:reset_workflow_command
      kotti-migrate-storage = kotti.filedepot:migrate_storages_command

      [pytest11]
      kotti = kotti.tests

      [pyramid.scaffold]
      kotti=kotti.scaffolds:KottiPackageTemplate
      """,
      extras_require={
          'testing': tests_require,
          'development': development_requires,
          'docs': docs_require,
          },
      )
