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
    'alembic==0.5.0',
    'babel==0.9.6',
    'beaker==1.6.4',
    'chameleon==2.11',
    'colander==1.0a2',
    'deform-bootstrap==0.2.9',
    'deform==0.9.7',
    'docopt==0.6.1',
    'fanstatic==1.0a',
    'formencode',
    'formencode==1.2.6',
    'html2text==3.200.3',
    'js.angular==1.1.2',
    'js.bootstrap==2.3.1',
    'js.chosen==0.9.11',
    'js.deform-bootstrap==0.2.6',
    'js.deform==0.9.7',
    'js.fineuploader==3.3.0',
    'js.html5shiv==3.6.2-1',
    'js.jquery',
    'js.jquery-form==3.09',
    'js.jquery-maskedinput==1.3.1',
    'js.jquery-maskmoney==1.4.1',
    'js.jquery-tablednd==0.4',
    'js.jquery-timepicker-addon==1.3-1',
    'js.jquery==1.9.1',
    'js.jquery_form',
    'js.jquery_tablednd',
    'js.jquery_timepicker_addon',
    'js.jqueryui-tagit==2.0.24-2',
    'js.jqueryui==1.10.3',
    'js.jqueryui_tagit',
    'js.tinymce==4.0.2',
    'kotti-tinymce==0.4.2',
    'lingua==1.5',
    'mako==0.8.0',
    'markupsafe==0.15',
    'pastedeploy==1.5.0',
    'peppercorn==0.4',
    'pillow==2.0.0',
    'plone.scale==1.3.1',
    'polib==1.0.3',
    'py-bcrypt==0.3',
    'pygments==1.6',
    'pyramid-chameleon==0.1',
    'pyramid-deform==0.2a5',
    'pyramid-mailer==0.11',
    'pyramid-tm==0.7',
    'pyramid-zcml==1.0.0',
    'pyramid==1.5a2',
    'pyramid_beaker',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'pyramid_zcml',
    'pytz==2013b',
    'repoze.lru==0.6',
    'repoze.sendmail==4.0',
    'repoze.workflow==0.6.1',
    'repoze.zcml==0.4',
    'sqlalchemy==0.8.2',
    'transaction==1.4.1',
    'translationstring==1.1',
    'unidecode==0.04.12',
    'venusian==1.0a8',
    'waitress==0.8.5',
    'webob==1.2.3',
    'xlrd==0.9.2',
    'xlwt==0.7.5',
    'zope.component==4.1.0',
    'zope.configuration==4.0.2',
    'zope.deprecation==4.0.2',
    'zope.event==4.0.2',
    'zope.i18nmessageid==4.0.2',
    'zope.interface==4.0.5',
    'zope.schema==4.3.2',
    'zope.sqlalchemy==0.7.2',
    ]

tests_require = [
    'WebTest',
    'mock',
    'pyquery',
    'pytest>=2.4.2',
    'pytest-cov',
    'pytest-pep8!=1.0.3',
    'pytest-xdist',
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
    ]

if sys.version_info[:3] < (2, 7, 0):
    install_requires.append('ordereddict')

setup(name='Kotti',
      version='0.10dev',
      description="A user-friendly, light-weight and extensible web content management system. Based on Pyramid and SQLAlchemy.",
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
      kotti = kotti.tests
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
