import codecs
import os

from setuptools import find_packages
from setuptools import setup

version = '2.0.0b1'
description = "A high-level, Pythonic web application framework based on " \
              "Pyramid and SQLAlchemy.  It includes an extensible Content " \
              "Management System called the Kotti CMS."
author = 'Kotti Developers'
author_email = 'kotti@googlegroups.com'
url = 'http://kotti.pylonsproject.org/'
keywords = 'kotti web cms wcms pylons pyramid sqlalchemy bootstrap'
license = "BSD-derived (http://www.repoze.org/LICENSE.txt)"


install_requires = [
    'Babel',
    'Chameleon>=2.7.4',  # Fixes error when raising HTTPFound
    'alembic>=0.8.0',
    'bleach>=2.1.2',  # html5lib 1.0 support
    'bleach-whitelist',
    'colander>=1.3.2',
    'deform>=2.0.5',  # fixes file upload on py3 - uncomment after 2.0.5 is released  # noqa
    'docopt',
    'fanstatic>=1.0.0',
    'filedepot',
    'formencode>=2.0.0a',
    'html2text',
    'iso8601==0.1.11',  # rq.filter: !=0.1.12
    'js.angular',
    'js.bootstrap>=3.0.0',
    'js.deform>=2.0a2-2',
    'js.fineuploader',
    'js.html5shiv',
    'js.jquery<2.0.0.dev',  # rq.filter: <2.0
    'js.jquery_form',
    'js.jquery_tablednd',
    'js.jquery_timepicker_addon',
    'js.jqueryui>=1.8.24',
    'js.jqueryui_tagit',
    'lingua>=1.3',
    'py_bcrypt',
    'pyramid>=1.9',
    'pyramid_beaker',
    'pyramid_chameleon',
    'pyramid_deform>=0.2a3',  # language and template path config includeme
    'pyramid_mailer',
    'pyramid_tm',
    'pyramid_zcml>=1.1.0',  # py3 compat
    'repoze.lru',
    'repoze.workflow>=1.0b1',
    'repoze.zcml>=1.0b1',
    'rfc6266-parser',
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
    'Pillow',  # thumbnail filter in depot tween tests
    'py>=1.4.29',
    'pyquery',
    'pytest>=3.0.0',
    'pytest-cov',
    'pytest-pep8!=1.0.3',
    'pytest-travis-fold',
    'pytest-virtualenv',
    'pytest-xdist',
    'tox',
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
    'setuptools-git',  # needed to make "python setup.py install" on rtd.
    'pytest',  # needed for kotti.testing apidocs
    ]

setup_requires = [
    'setuptools_git>=0.3',
]


here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """ Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.

    Copied from
    https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
    """

    with codecs.open(os.path.join(here, *parts), "rb", "utf-8") as f:
        return f.read()


setup(name='Kotti',
      version=version,
      description=description,
      long_description='\n\n'.join([read('README.rst'),
                                    read('AUTHORS.txt'),
                                    read('CHANGES.txt'), ]),
      classifiers=[
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
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: Implementation',
          'Programming Language :: Python :: Implementation :: CPython',
          # 'Programming Language :: Python :: Implementation :: PyPy',
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
      author=author,
      author_email=author_email,
      url=url,
      keywords=keywords,
      license=license,
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      setup_requires=setup_requires,
      tests_require=tests_require,
      entry_points={
          'paste.app_factory': [
              'main = kotti:main',
          ],
          'fanstatic.libraries': [
              'kotti = kotti.fanstatic:lib_kotti',
          ],
          'console_scripts': [
              'kotti-migrate = kotti.migrate:kotti_migrate_command',
              'kotti-reset-workflow = kotti.workflow:reset_workflow_command',
              'kotti-migrate-storage = kotti.filedepot:migrate_storages_command',  # noqa
          ],
          'pytest11': [
              'kotti = kotti.tests',
          ],
      },
      extras_require={
          'testing': tests_require,
          'development': development_requires,
          'docs': docs_require,
          },
      )
