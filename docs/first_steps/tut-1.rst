.. _tut-1:

Tutorial part 1: Customize the look and feel
============================================

Let's learn by example.  We'll create an add-on package with which we
will:

- change the look and feel of Kotti by registering an additional CSS file
- add content types and forms
- add a portlet

.. note::

    If you're having trouble going through this tutorial, please post
    a message to the `mailing list`__ or join the `#kotti channel on
    irc.freenode.net`__ to chat with other Kotti users who might be
    able to help.

In this part of the tutorial, we'll concentrate on how to create the
new add-on, how to install and register it with our site, and how
static resources are managed in Kotti.

__ mailing list: http://groups.google.com/group/kotti
__ irc://irc.freenode.net/#kotti


Creating the add-on package
---------------------------

To create our add-on, we'll use a starter template from
``kotti_paster``.  For this, we'll need to first install the
``kotti_paster`` package into our virtualenv (the one that created
during the :ref:`installation`).

.. code-block:: bash

  bin/pip install kotti_paster

With ``kotti_paster`` installed, we can now create the skeleton for
our add-on package:

.. code-block:: bash

  bin/paster create -t kotti_addon kotti_mysite

Running this command, it will ask us a number of questions.  We just
hit enter for every question to accept the defaults.  At the end,
we'll find a new directory called ``kotti_mysite`` in our current
working directory.  This directory contains our new add-on package.

Installing our new add-on
-------------------------

To install our add-on (or any add-on, for that matter) into our Kotti
site, we'll need to do two things:

- install the package into our virtualenv
- include the package inside our site's ``app.ini``

.. note::

  Why two steps?  Installation of our add-on as a Python package is
  different to activating the add-on in our site.  Just because a
  Kotti add-on is installed and can be imported doesn't mean we want
  all our sites to use it.

To install the package into the virtualenv, we'll change into the new
``kotti_mysite`` directory, and issue a ``python setup.py develop``.
This will install the package in *development mode*:

.. code-block:: bash

  cd kotti_mysite
  ../bin/python setup.py develop

Step two is configuring our Kotti site to include our new
``kotti_mysite`` package.  To do this, open the ``app.ini`` file which
you downloaded during :ref:`installation`.  Find the line that says:

.. code-block:: ini

  kotti.configurators = kotti_tinymce.kotti_configure

And add ``kotti_mysite.kotti_configure`` to it:

.. code-block:: ini

  kotti.configurators =
      kotti_tinymce.kotti_configure
      kotti_mysite.kotti_configure

Now you're ready to fire up the Kotti site again:

.. code-block:: bash

  cd ..
  bin/pserve app.ini

Visit the site in your browser and notice how the the title now has a
shadow.

Adding CSS files
----------------

How is the color changed?  Take a look into the directory
``kotti_mysite/kotti_mysite/static/`` -- this is where the CSS file
lives.

How is it hooked up with Kotti?  Kotti uses fanstatic_ for managing
its static resources.  fanstatic has a number of cool features, you
may want to check out their homepage to find out more.

Take a look at ``kotti_mysite/kotti_mysite/static.py`` to see how the
creation of the necessary fanstatic components is done:

.. code-block:: python

  from fanstatic import Group
  from fanstatic import Library
  from fanstatic import Resource
  from kotti.fanstatic import base_css

  library = Library("kotti_mysite", "static")
  kotti_mysite_css = Resource(library, "style.css", depends=[base_css])
  kotti_mysite_group = Group([kotti_mysite_css])

The ``depends=[base_css]`` argument to ``Resource`` is required so
that your CSS is included after Kotti's own so that Kotti's styles can
be overridden.

If you wanted to add a JavaScript file, you would do this very
similarly.  Maybe like this:

.. code-block:: python

  kotti_mysite_js = Resource(library, "script.js")

And change the last line to:

.. code-block:: python

  kotti_mysite_group = Group([kotti_mysite_css, kotti_mysite_js])

.. _fanstatic: http://www.fanstatic.org/

Configuring the package with ``kotti.configurators``
----------------------------------------------------

Remember when we added ``kotti_mysite.kotti_configure`` to the
``kotti.configurators`` setting in the ``app.ini`` configuration file?
This is how we told Kotti to call additional code on start-up, so that
add-ons have a chance to configure themselves.  The function in
``kotti_mysite`` that's called on application start-up lives in
``kotti_mysite/kotti_mysite/__init__.py``.  Let's take a look:

.. code-block:: python

  def kotti_configure(settings):
      settings['kotti.fanstatic.view_needed'] += ' kotti_mysite.static.kotti_mysite_group'

Here, ``settings`` is a dictionary with all configuration variables in
the ``[app:kotti]`` section out our ``app.ini``, plus the defaults.
The values of this dictionary are merely strings.  Notice how we add
to the string ``kotti.fanstatic.view_needed`` (leaving a space between
whatever was the value and what we add).

This ``kotti.fanstatic.view_needed`` setting, in turn, controls which
resources are loaded in the public interface (as opposed to the edit
interface).

As you might have guessed, we could have also completely replaced all
of Kotti's resources for the public interface by overriding the
``kotti.fanstatic.view_needed`` setting instead of adding to it, like
so:

.. code-block:: python

  def kotti_configure(settings):
      settings['kotti.fanstatic.view_needed'] = ' kotti_mysite.static.kotti_mysite_group'

This is useful if you've built your own custom bootstrap theme.
Alternatively, you can completely :ref:`override the master template
<asset_overrides>` for even more control (e.g. if you don't want to
use Bootstrap).

See also :ref:`configuration` for a full list of Kotti's configuration
variables, and :ref:`static resources` for a more complete discussion
of how Kotti handles static resources through fanstatic.

In the :ref:`next part <tut-2>` of the tutorial, we'll add our first
content types, and add forms for them.
