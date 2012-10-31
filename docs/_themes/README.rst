sphinx-bootstrap
================

`Sphinx <http://sphinx.pocoo.org/>`_ theme adapted from `Twitter's Bootstrap <twitter.github.com/bootstrap/>`_

Demo
----
Projects using it:
~~~~~~~~~~~~~~~~~~
- `EngineAuth <http://code.scotchmedia.com/engineauth>`_
- `Vixo Documentation <http://documentation.vixo.com>`_

Install
-------

1. Copy the ``sphinx-boostrap`` fold to your ``themes`` directory.

2. Add the following lines to your ``config.py`` file::

    # The theme to use for HTML and HTML Help pages.  See the documentation for
    # a list of builtin themes.
    html_theme = 'sphinx-bootstrap'

    # Theme options are theme-specific and customize the look and feel of a theme
    # further.  For a list of options available for each theme, see the
    # documentation.
    html_theme_options = {
        'analytics_code': 'UA-00000000-1',
        'github_user': 'scotch',
        'github_repo': 'sphinx-bootstrap',
        'twitter_username': 'scotchmedia',
        'home_url': 'http://code.scotchmedia.com/sphinx-bootstrap',
        'disqus_shortname': 'scotchmedia',
    }

3. Choose your theme. Edit `sphinx-bootstrap.css`. At the top of the file you will see this::

    Uncomment the theme you would like to use.

    @import "bootstrap-engineauth.min.css";
    /*@import "bootstrap-default.min.css";*/
    /*@import "bootstrap-sapling.css";*/

Themes
------

New themes can be created using the `bootstrap customizer <http://twitter.github.com/bootstrap/customize.html>`_

Once you have created a custom theme include it in that static
directory and change the @import link to include your file. If you think the
themes is one that others will like. Send a pull request.



License
-------

sphinx-bootstrap
~~~~~~~~~~~~~~~~
Code licensed under the `Apache License v2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_. Documentation licensed under `CC BY 3.0 <http://creativecommons.org/licenses/by/3.0/>`_

Twitter's Bootstrap
~~~~~~~~~~~~~~~~~~~
Code licensed under the `Apache License v2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_. Documentation licensed under `CC BY 3.0 <http://creativecommons.org/licenses/by/3.0/>`_

