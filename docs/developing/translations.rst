.. _translations:

Translations
============

You can `find the list of Kotti's translations here`_.  Kotti uses
`GNU gettext`_ and .po files for internationalization.

You can set the ``pyramid.default_locale_name`` in your configuration
file to choose which language Kotti should serve the user interface
(see :ref:`user interface language`).

In order to compile your .po files to .mo files, do:

.. code-block:: bash

  bin/python setup.py compile_catalog --use-fuzzy

To extract messages and update the existing .pot and .po files, do:

.. code-block:: bash

  bin/python setup.py extract_messages update_catalog

.. _find the list of Kotti's translations here: https://github.com/Kotti/Kotti/tree/master/kotti/locale
.. _GNU gettext: http://www.gnu.org/software/gettext/
