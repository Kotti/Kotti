import os
import subprocess
import sys

from setuptools import setup
from setuptools import find_packages
from setuptools import Command

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

install_requires = [
    'pyramid>=1.2',
    'pyramid_tm',
    'repoze.lru',
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

tests_require = [
    'mock',
    'pytest-cov',
    'pytest-xdist',
    'wsgi_intercept',
    'zope.testbrowser',
    'pytest',
    ]

if sys.version_info[:3] < (2,7,0):
    install_requires.append('ordereddict')

class PyTest(Command):
    user_options = []
    initialize_options = finalize_options = lambda self: None
    errno = 1

    def run(self):
        script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'bin', 'py.test')
        errno = subprocess.call([sys.executable, script])
        raise SystemExit(errno)

setup(name='Kotti',
      version='0.2.6',
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
      author='Daniel Nouri and contributors',
      author_email='kotti@googlegroups.com',
      url='https://github.com/dnouri/Kotti',
      keywords='web kotti cms wcms pylons pyramid',
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      cmdclass={'test': PyTest},
      install_requires=install_requires + tests_require,
      #tests_require=tests_require,
      entry_points = """\
      [paste.app_factory]
      main = kotti:main
      """,
      paster_plugins=['pyramid'],
      )
