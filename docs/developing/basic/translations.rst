.. _translations:

Translations
============

You can `find the list of Kotti's translations here`_.
Kotti uses `GNU gettext`_ and .po files for internationalization.

You can set the ``pyramid.default_locale_name`` in your configuration file to choose which language Kotti should serve the user interface (see :ref:`user interface language`).

Extraction of new messages into the ``.pot`` file, updating the existing ``.po`` files and compiling them to ``.mo`` files is all done with subsequent runs of the included ``i18n.sh`` script:

.. code-block:: bash

  ./i18n.sh

To add a new translations run:

.. code-block:: bash

  ./i18n.sh <2 letter code of the new language>

.. _find the list of Kotti's translations here: https://github.com/Kotti/Kotti/tree/master/kotti/locale
.. _GNU gettext: http://www.gnu.org/software/gettext/
