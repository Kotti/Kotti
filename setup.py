import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

install_requires = [
    'pyramid',
    'repoze.tm2>=1.0b1', # default_commit_veto
    'sqlalchemy>=0.7b2',
    'chameleon<1.2.999', # more recent versions have compat issues right now
    'zope.sqlalchemy',
    'formencode',
    'deform>=0.10dev',
    'colander>=0.9.3dev',
    'WebError',
    'Babel',
    'pyramid_mailer',
    ]

tests_require = ['nose', 'coverage', 'wsgi_intercept', 'zope.testbrowser']

install_requires.extend(tests_require) # for buildout

dependency_links = [
    'http://prdownloads.sourceforge.net/sqlalchemy/SQLAlchemy-0.7b2.tar.gz?download',
    'http://danielnouri.org/packages/',
    ]

if sys.version_info[:3] < (2,5,0):
    install_requires.append('pysqlite')

if sys.version_info[:3] < (2,7,0):
    install_requires.append('ordereddict')

setup(name='Kotti',
      version='0.1a9',
      description="A user-friendly, light-weight and extensible web content management system.  Written in Python, based on Pyramid and SQLAlchemy.",
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: Repoze Public License",
        ],
      author='Daniel Nouri',
      author_email='daniel.nouri@gmail.com',
      url='https://github.com/dnouri/Kotti',
      keywords='web kotti cms wcms pylons pyramid',
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      dependency_links=dependency_links,
      setup_requires=['nose'],
      install_requires=install_requires,
      tests_require=tests_require,
      test_suite="kotti",
      entry_points = """\
      [paste.app_factory]
      main = kotti:main
      """,
      paster_plugins=['pyramid'],
      )
