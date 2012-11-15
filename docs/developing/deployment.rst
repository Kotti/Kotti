.. deployment:

Deployment
==========

Kotti deployment is not different from deploying any other WSGI app.  You have
a bunch of options on multiple layers: OS, RDBMS, Webserver, etc.

This document assumes the following Stack:

OS
    Ubuntu 12.04
Webserver
    Nginx
RDBMS
    PostgreSQL
Kotti
    | latest version available on PyPI
    | installed in its own virtualenv
    | deployed in an uWSGI application container

Manual installation
-------------------



Fabfile
-------

**WARNING: this is only an example.  Do not run this unmodified against a host
that is intended to do anything else or things WILL break!**

For your convenience there is a `fabric`_ file that automates all of the above.
If you don't know what fabric is and how it works read their documentation
first.

On your local machine make a separate virtualenv first and install the
``fabric`` and ``fabtools`` packages into that virtualenv::

    mkvirtualenv kotti_deployment && cdvirtualenv
    pip install fabric fabtools

Get the fabfile::

    wget https://gist.github.com/gists/4079191/download

Without modifications it will only work against a fresh install of Ubuntu 12.04
with SSH service enabled.  Read and modify the file to fit your needs.  Then run
it against your server::

    fab deploy_kotti

You're done.  Everything is installed and configured to serve Kotti under
http://kotti.yourdomain.com/

.. _fabric: http://docs.fabfile.org/
