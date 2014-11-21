.. _understanding-kotti-startup:

Understanding Kotti's startup phase
===================================

1.  When a Kotti application is started the :func:`kotti.main` function is
    called by the WSGI server and is passed a ``settings`` dictionary that
    contains all key / value pairs from the ``[app:kotti]`` section of the
    ``*.ini`` file.

2.  The ``settings`` dictionary is passed to :func:`kotti.base_configure`.
    This is where the main work happens:

    1.  Every key in `kotti.conf_defaults` that is not in the ``settings``
        dictionary (i.e. that is not in the ``.ini`` file) is copied to the
        ``settings`` dictionary, together with the default value for that key.

    2.  Add-on initializations: all functions that are listed in the
        ``kotti.configurators`` parameter are resolved and called.

    3.  ``pyramid.includes`` are removed from the ``settings`` dictionary for
        later processing, i.e. **after** ``kotti.base_includes``.

    4.  A class:`pyramid.config.Configurator` is instanciated with the remaining
        ``settings``.

    5.  The ``kotti.base_includes`` (containing various Kotti subsystems, such
        as ``kotti.events``, ``kotti.views``, etc.) are passed to
        ``config.include``.

    6.  The ``pyramid.includes`` that were removed from the ``settings``
        dictionary in step 2.3 are processed.

    7.  The ``kotti.zcml_includes`` are processed.

3.  The SQLAlchemy engine is created with the connection URL that is defined
    in the sqlalchemy.url parameter in the ``.ini`` file.

4.  The fully configured WSGI application is returned to the WSGI server and
    is ready to process requests.
