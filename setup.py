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
    'deform',
    'WebError',
    ]

tests_require = ['nose', 'coverage', 'wsgi_intercept', 'zope.testbrowser']

install_requires.extend(tests_require) # for buildout

if sys.version_info[:3] < (2,5,0):
    install_requires.append('pysqlite')

if sys.version_info[:3] < (2,7,0):
    install_requires.append('ordereddict')

setup(name='Kotti',
      version='0.1a6',
      description="A friendly, light-weight web content management system (WCMS).  Written in Python, based on Pyramid and SQLAlchemy.",
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Daniel Nouri',
      author_email='daniel.nouri@gmail.com',
      url='https://github.com/dnouri/Kotti',
      keywords='web pylons pyramid cms wcms',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      dependency_links=['http://prdownloads.sourceforge.net/sqlalchemy/SQLAlchemy-0.7b2.tar.gz?download'],
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
