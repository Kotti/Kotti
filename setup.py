import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'repoze.tm2>=1.0b1', # default_commit_veto
    'sqlalchemy',
    'zope.sqlalchemy',
    'deform',
    'WebError',
    'nose',
    ]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='Kotti',
      version='0.1a2',
      description="A user-friendly web content management system (WCMS).  Written in Python, based on Pyramid and SQLAlchemy.",
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
      install_requires = requires,
      tests_require = requires + [
          'coverage', 'wsgi_intercept', 'zope.testbrowser'],
      test_suite="kotti",
      entry_points = """\
      [paste.app_factory]
      main = kotti:main
      """,
      paster_plugins=['pyramid'],
      )
