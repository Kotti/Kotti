# -*- coding: utf-8 -*-

import codecs
import os

from setuptools import find_packages
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    """ Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.

    Copied from
    https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
    """

    with codecs.open(os.path.join(here, *parts), "rb", "utf-8") as f:
        return f.read()


install_requires = [
    'Babel',
    'Chameleon>=2.7.4',  # Fixes error when raising HTTPFound
    'alembic>=0.8.0',
    'bleach',
    'bleach-whitelist',
    'colander<1.3',  # until https://github.com/Pylons/colander/pull/272 is merged and released  # noqa
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
    'kotti_image',
    'lingua>=1.3',
    'py_bcrypt',
    'pyramid>=1.5',  # needed for ``request.has_permission``
    'pyramid_beaker',
    'pyramid_chameleon',
    'pyramid_deform>=0.2a3',  # language and template path config includeme
    'pyramid_mailer',
    'pyramid_tm',
    'pyramid_zcml',
    'repoze.lru',
    'repoze.workflow>=1.0b1',
    'rfc6266',
    'sqlalchemy>=1.0.0',
    'sqlalchemy-utils',
    'transaction>=1.1.0',
    'unidecode',
    'usersettings',
    'waitress',
    'zope.deprecation',
    'zope.interface',
    'zope.sqlalchemy',
    ]

tests_require = [
    'WebTest',
    'mock',
    'py>=1.4.29',
    'pyquery',
    'pytest>=3.0.0',
    'pytest-cov',
    'pytest-pep8!=1.0.3',
    'pytest-travis-fold',
    'pytest-virtualenv',
    'pytest-warnings',
    'pytest-xdist',
    'virtualenv',  # needed for scaffolding tests
    'zope.testbrowser>=5.0.0',
    ]

development_requires = [
    'check-manifest',
    'pipdeptree',
    'pyramid_debugtoolbar',
]

docs_require = [
    'Sphinx',
    'docutils',
    'repoze.sphinx.autointerface',
    'sphinx_rtd_theme',
    ]

setup_requires = [
    'setuptools_git>=0.3',
]

setup(name='Kotti',
      version='1.3.0',
      description="A high-level, Pythonic web application framework based on Pyramid and SQLAlchemy.  It includes an extensible Content Management System called the Kotti CMS.",  # noqa
      long_description='\n\n'.join([
          read('README.rst'),
          read('AUTHORS.txt'),
          read('CHANGES.txt'),
      ]),
      classifiers=[
          # 'Development Status :: 3 - Alpha',
          # 'Development Status :: 4 - Beta',
          'Development Status :: 5 - Production/Stable',
          'Environment :: Web Environment',
          'Framework :: Pylons',
          'Framework :: Pyramid',
          'License :: Repoze Public License',
          'Natural Language :: Dutch',
          'Natural Language :: English',
          'Natural Language :: French',
          'Natural Language :: German',
          'Natural Language :: Italian',
          'Natural Language :: Japanese',
          'Natural Language :: Polish',
          'Natural Language :: Portuguese',
          'Natural Language :: Swedish',
          'Operating System :: POSIX',
          'Operating System :: Unix',
          # 'Programming Language :: JavaScript',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          # 'Programming Language :: Python :: 3',
          # 'Programming Language :: Python :: 3.3',
          # 'Programming Language :: Python :: 3.4',
          # 'Programming Language :: Python :: 3.5',
          # 'Programming Language :: Python :: 3.6',
          'Programming Language :: SQL',
          'Topic :: Internet',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',  # noqa
          'Topic :: Internet :: WWW/HTTP :: WSGI',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries :: Application Frameworks',  # noqa
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
      setup_requires=setup_requires,
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
