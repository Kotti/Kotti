.. _contributing:

Contributing
============

The Kotti project can use your help in developing the software, requesting features, reporting bugs, writing developer and end-user documentation -- the usual assortment for an open source project.

Please devote some of your time to the project.

Contributing to the Code Base
-----------------------------

To contribute to Kotti itself, and to test and run against the master branch (the current development code base), first create an account on GitHub if you don't have one.
Fork `Kotti`_ to your github account, and follow the usual steps to get a local clone, with ``origin`` as your fork, and with ``upstream`` as the Kotti/Kotti repo.
Then, you will be able to make branches for contributing, etc.
Please read the docs on GitHub if you are new to development, but the steps, after you have your own fork, would be something like this:

.. code-block:: bash

  git clone https://github.com/your_github/Kotti.git

  cd Kotti

  git remote add upstream git://github.com/Kotti/Kotti.git

Now you should be set up to make branches for this and that, doing a pull request from a branch, and the usual git procedures.
You may wish to read the `GitHub fork-a-repo help`_.

To run and develop within your clone, do these steps:

.. code-block:: bash

  virtualenv . --no-site-packages

  bin/python setup.py develop

This will create a new virtualenv "in place" and do the python develop steps to
use the Kotti code in the repo.

Run ``bin/pip install kotti_someaddon``, and add a kotti_someaddon entry to ``app.ini``, as you would do normally, to use add-ons.

You may wish to learn about the `virtualenvwrapper system`_ if you have several
add-ons you develop or contribute to.
For example, you could have a development area devoted to Kotti work, ~/kotti, and in there you could have clones of repos for various add-ons.
And for each, or in some combination, you would use virtualenvwrapper to create virtualenvs for working with individual add-ons or Kotti-based projects.
``virtualenvwrapper`` will set these virtualenvs up, by default, in a directory within your home directory.
With this setup, you can do ``workon kotti_this`` and ``workon kotti_that`` to switch between different virtualenvs.
This is handy for maintaining different sets of dependencies and customizations, and for staying organized.

Contributing to Developer Docs
------------------------------

Kotti uses the `Sphinx tool`_, using `reStructuredText`_ to write documents,
stored in docs/ in a directory structure with .rst files.
Use the normal git procedures for first making a branch, e.g., ``navigation_docs``, then after making changes, commit, push to this branch on your fork,  and do a pull request from there, just as you would for contributing to the code base.

In your Kotti clone you can install the requirements for building and viewing the documents locally:

.. code-block:: bash

  python setup.py docs

  cd docs/

  make html

Then you can check the .html files in the _build/ directory locally, before you
do an actual pull request.

The rendered docs are built and hosted on readthedocs.org.

Contributing to User Docs
-------------------------

The `Kotti User Manual`_ also uses Sphinx and reStructuredText, but there is a bit more to the procedure, because several additional tools are used.
`Selenium`_ is used for making screen captures, and thereby helps to actually test Kotti in the process.
`blockdiag`_ is used to make flow charts and diagrams interjected into the docs.

Please follow the readme instructions in the `Kotti User Manual repo`_ to get set up for contributing to the user manual.
Of course, you can do pull requests that change only the text, but please get set up for working with graphics also, because this is a way to do the important task of keeping Kotti user docs up-to-date, guaranteed to have graphics in sync with the latest Kotti version.

The rendered docs are built and hosted on readthedocs.org.

.. _blockdiag: http://blockdiag.com
.. _GitHub fork-a-repo help: https://help.github.com/articles/fork-a-repo
.. _Kotti User Manual repo: https://github.com/Kotti/kotti_user_manual
.. _Kotti User Manual: https://kotti-user-manual.readthedocs.io
.. _Kotti: github.com/Kotti/Kotti
.. _reStructuredText: http://sphinx-doc.org/rest.html
.. _Selenium: https://selenium-python.readthedocs.io
.. _Sphinx tool: https://sphinx.readthedocs.io
.. _virtualenvwrapper system: https://virtualenvwrapper.readthedocs.io
