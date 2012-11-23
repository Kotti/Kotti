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
    'js.deform>=0.9.5-4',
    'js.deform_bootstrap>=0.2.4-1',
    'js.jquery',
    'js.jquery_form',
    'js.jquery_timepicker_addon',
    'js.jqueryui>=1.8.24',
    'js.jqueryui_tagit',
    'kotti_tinymce>=0.3.1',
    'lingua>=1.3',
    'Pillow',  # dependency of plone.scale
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
    'sqlalchemy>=0.7.6',
    'transaction>=1.1.0',
    'unidecode',
    'waitress',
    'zope.browserresource',
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

docs_require = [
    'Sphinx',
    'docutils',
    'repoze.sphinx.autointerface',
    ]

if sys.version_info[:3] < (2, 7, 0):
    install_requires.append('ordereddict')

setup(name='Kotti',
      version='0.8dev2',
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
      kotti = kotti.fanstatic:lib_kotti

      [console_scripts]
      kotti-migrate = kotti.migrate:kotti_migrate_command
      kotti-reset-workflow = kotti.workflow:reset_workflow_command

      [pytest11]
      kotti = kotti.tests.configure
      """,
      extras_require={
          'testing': tests_require,
          'development': development_requires,
          'docs': docs_require,
          },
      message_extractors={'kotti': [
            ('**.py', 'lingua_python', None),
            ('**.zcml', 'lingua_xml', None),
            ('**.pt', 'lingua_xml', None),
            ]},
      )
