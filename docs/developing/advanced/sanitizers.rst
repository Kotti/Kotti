.. _sanitizers:

Sanitizers
==========

Kotti provides a mechanism to *sanitize* arbitrary strings.

You can configure *available* sanitizers via ``kotti.sanitizers``.
This setting takes a list of strings, with each specifying a ``name:callable`` pair.
``name`` is the name under which this sanitizer is registered.
``callable`` is a dotted path to a function taking an unsanitized string and returning a sanitized version of it.

The default configuration is::

  kotti.sanitizers =
      xss_protection:kotti.sanitizers.xss_protection
      minimal_html:kotti.sanitizers.minimal_html
      no_html:kotti.sanitizers.no_html

For thorough explaination of the included sanitizers see :mod:`kotti.sanitizers`.

Explicit sanitization
---------------------

You can explicitly use any configured sanitizer like this::

  from kotti.sanitizers import sanitize

  sanitzed = sanitize(unsanitized, 'xss_protection')

The sanitize function is also available as a method of the :class:`kotti.views.util.TemplateAPI`.
This is just a convenience wrapper to ease usage in templates::

  ${api.sanitize(context.foo, 'minimal_html')}

Sanitize on write (implicit sanitization)
-----------------------------------------

The second setting related to sanitization is ``kotti.sanitize_on_write``.
It defines, for the specified resource classes, the attributes that are sanitized and the sanitizers that will be used when the attributes are mutated and flushed.

This setting takes a list of ``dotted_path:sanitizer_name(s)`` pairs.
``dotted_path`` is a dotted path to a resource class attribute that will be sanitized implicitly with the respective sanitizer(s) upon write access.
``sanitizer_name(s)`` is a comma separated list of available sanitizer names as configured above.

Kotti will setup :ref:`listeners <events>` for the :class:`kotti.events.ObjectInsert` and :class:`kotti.events.ObjectUpdate` events for the given classes and attach a function that filters the respective attributes with the specified sanitizer.

This means that *any* write access to configured attributes through your application (also within correctly setup command line scripts) will be sanitized *implicitly*.

The default configuration is::

  kotti.sanitize_on_write =
      kotti.resources.Document.body:xss_protection
      kotti.resources.Content.title:no_html

You can also use multiple sanitizers::

  kotti.sanitize_on_write =
      kotti.resources.Document.body:xss_protection,some_other_sanitizer

Implementing a custom sanitizer
-------------------------------

A sanitizer is just a function that takes and returns a string.
It can be as simple as::

  def no_dogs_allowed(html):
      return html.replace('dogs', 'cats')

  no_dogs_allowed('<p>I love dogs.</p>')
  ... '<p>I love cats.</p>'

You can also look at :mod:`kotti.sanitizers` for examples.
