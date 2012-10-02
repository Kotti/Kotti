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
    'alembic',
    'Babel',
    'Chameleon>=2.7.4',  # Fixes error when raising HTTPFound
    'colander>=0.9.3',
    'deform>=0.9.4',  # deform_bootstrap (needs fixing there)
    'deform_bootstrap>=0.1',  # checked_input widget
    'docopt',
    'formencode',
    'html2text',
    'js.bootstrap>=2.1.5',
    'js.jquery',
    'js.jquery_timepicker_addon',
    'js.jqueryui',
    'js.jqueryui_tagit',
    'kotti_tinymce>=0.2.3',
    'lingua>=1.3',
    'Pillow',  # indirect dependency of plone.scale (that doesn't declare this dependency itself)
    'plone.i18n<2.0',  # >= 2.0 adds a huge number of dependencies
    'plone.scale',  # needed for image resizing capabilities
    'py-bcrypt',
    'pyramid>=1.3',  # needed for kotti_tinymce
    'pyramid_beaker',
    'pyramid_debugtoolbar',
    'pyramid_deform>=0.2a3',  # language and template path config includeme
    'pyramid_mailer',
    'pyramid_tm',
    'pyramid_zcml',
    'repoze.lru',
    'repoze.workflow',
    'sqlalchemy>=0.7.6',  # avoid "Table 'local_groups' is already defined" error
    'transaction>=1.1.0',  # ask c-neumann :-)
    'waitress',
    'zope.deprecation',
    'zope.sqlalchemy',
    ]

tests_require = [
    'WebTest',
    'mock',
    'pytest',
    'pytest-cov',
    'pytest-pep8',
    'pytest-xdist',
    'wsgi_intercept',
    'zope.testbrowser',
    ]

development_requires = [
    'minify',
    ]

if sys.version_info[:3] < (2, 7, 0):
    install_requires.append('ordereddict')

setup(name='Kotti',
      version='0.7.2',
      description="Kotti is a high-level, 'Pythonic' web application framework. It includes a small and extensible CMS application called the Kotti CMS.",
      long_description='\n\n'.join([README, AUTHORS, CHANGES]),
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: Repoze Public License",
        ],
      author='Kotti developers',
      author_email='kotti@googlegroups.com',
      url='http://kotti.pylonsproject.org',
      keywords='kotti web cms wcms pylons pyramid sqlalchemy bootstrap',
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      dependency_links=[
      ],
      entry_points="""\
      [paste.app_factory]
      main = kotti:main

      [fanstatic.libraries]
      kotti = kotti.static:lib_kotti
      deform = kotti.static:lib_deform
      deform_bootstrap = kotti.static:lib_deform_bootstrap

      [console_scripts]
      kotti-migrate = kotti.migrate:kotti_migrate_command
      kotti-reset-workflow = kotti.workflow:reset_workflow_command
      """,
      extras_require={
          'testing': tests_require,
          'development': development_requires,
          },
      message_extractors={'kotti': [
            ('**.py', 'lingua_python', None),
            ('**.zcml', 'lingua_xml', None),
            ('**.pt', 'lingua_xml', None),
            ]},
      )
