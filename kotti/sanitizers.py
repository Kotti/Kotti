# -*- coding: utf-8 -*-

"""
For a high level introduction and available configuration options
see :ref:`sanitizers`.
"""

from bleach import clean
from bleach_whitelist import all_styles
from bleach_whitelist import generally_xss_safe
from bleach_whitelist import markdown_attrs
from bleach_whitelist import markdown_tags
from bleach_whitelist import print_attrs
from bleach_whitelist import print_tags
from pyramid.util import DottedNameResolver

from kotti import get_settings
from kotti.events import objectevent_listeners
from kotti.events import ObjectInsert
from kotti.events import ObjectUpdate


def sanitize(html, sanitizer):
    """ Sanitize HTML

    :param html: HTML to be sanitized
    :type html: basestring

    :param sanitizer: name of the sanitizer to use
    :type sanitizer: str

    :result: sanitized HTML
    :rtype: unicode
    """

    sanitized = get_settings()['kotti.sanitizers'][sanitizer](html)

    return sanitized


def xss_protection(html):
    """ Sanitizer that removes tags that are not considered XSS safe.  See
    ``bleach_whitelist.generally_xss_unsafe`` for a complete list of tags that
    are removed.  Attributes and styles are left untouched.

    :param html: HTML to be sanitized
    :type html: basestring

    :result: sanitized HTML
    :rtype: unicode
    """

    sanitized = clean(
        html,
        tags=generally_xss_safe,
        attributes=lambda self, key, value: True,
        styles=all_styles,
        strip=True,
        strip_comments=True)

    return sanitized


def minimal_html(html):
    """ Sanitizer that only leaves a basic set of tags and attributes.  See
    ``bleach_whitelist.markdown_tags``, ``bleach_whitelist.print_tags``,
    ``bleach_whitelist.markdown_attrs``, ``bleach_whitelist.print_attrs`` for a
    complete list of tags and attributes that are allowed.  All styles are
    completely removed.

    :param html: HTML to be sanitized
    :type html: basestring

    :result: sanitized HTML
    :rtype: unicode
    """

    attributes = dict(zip(
        markdown_attrs.keys() + print_attrs.keys(),
        markdown_attrs.values() + print_attrs.values()))

    sanitized = clean(
        html,
        tags=markdown_tags + print_tags,
        attributes=attributes,
        styles=[],
        strip=True,
        strip_comments=True)

    return sanitized


def no_html(html):
    """ Sanitizer that removes **all** tags.

    :param html: HTML to be sanitized
    :type html: basestring

    :result: plain text
    :rtype: unicode
    """

    sanitized = clean(
        html,
        tags=[],
        attributes={},
        styles=[],
        strip=True,
        strip_comments=True)

    return sanitized


def _setup_sanitizers(settings):

    # step 1: resolve sanitizer functions and make ``kotti.sanitizers`` a
    # dictionary containing resolved functions

    if not isinstance(settings['kotti.sanitizers'], basestring):
        return

    sanitizers = {}

    for s in settings['kotti.sanitizers'].split():
        name, dottedname = s.split(':')
        sanitizers[name.strip()] = DottedNameResolver(None).resolve(dottedname)

    settings['kotti.sanitizers'] = sanitizers


def _setup_listeners(settings):

    # step 2: setup listeners

    for s in settings['kotti.sanitize_on_write'].split():
        dotted, sanitizers = s.split(':')

        classname, attributename = dotted.rsplit('.', 1)
        _class = DottedNameResolver(None).resolve(classname)

        def _create_handler(attributename, sanitizers):
            def handler(event):
                value = getattr(event.object, attributename)
                for sanitizer_name in sanitizers.split(','):
                    value = settings['kotti.sanitizers'][sanitizer_name](value)
                setattr(event.object, attributename, value)
            return handler

        objectevent_listeners[(ObjectInsert, _class)].append(
            _create_handler(attributename, sanitizers))
        objectevent_listeners[(ObjectUpdate, _class)].append(
            _create_handler(attributename, sanitizers))


def includeme(config):

    _setup_sanitizers(config.registry.settings)
    _setup_listeners(config.registry.settings)
