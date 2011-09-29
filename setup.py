import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

install_requires = [
    'pyramid>=1.2',
    'repoze.tm2>=1.0b1', # default_commit_veto
    'sqlalchemy>=0.7',
    'zope.sqlalchemy',
    'Chameleon>=2',
    'formencode',
    'deform>=0.9.2', # Chameleon 2
    'colander>=0.9.3',
    'Babel',
    'pyramid_mailer',
    'py-bcrypt',
    'pyramid_debugtoolbar',
    ]

tests_require = ['nose', 'coverage', 'wsgi_intercept', 'zope.testbrowser']

install_requires.extend(tests_require) # for buildout

if sys.version_info[:3] < (2,5,0):
    install_requires.append('pysqlite')

if sys.version_info[:3] < (2,7,0):
    install_requires.append('ordereddict')

setup(name='Kotti',
      version='0.2.2',
      description="A user-friendly, light-weight and extensible web content management system.  Written in Python, based on Pyramid and SQLAlchemy.",
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
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
