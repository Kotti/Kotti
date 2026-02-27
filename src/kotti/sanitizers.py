""" For a high level introduction and available configuration options
see :ref:`sanitizers`.
"""
import warnings
from typing import Dict
from typing import Union

import nh3
from pyramid.config import Configurator
from pyramid.util import DottedNameResolver

from kotti import get_settings
from kotti.events import ObjectInsert
from kotti.events import ObjectUpdate
from kotti.events import objectevent_listeners


# XSS-safe tags — curated set based on generally_xss_safe from bleach_allowlist,
# minus 'style' (causes nh3 PanicException) and 'script' (content always removed by
# nh3). This is a tightened allowlist per CONTEXT.md: excludes form/input/button
# elements and other potentially risky interactive tags that were in bleach_allowlist
# but are not needed for CMS content.
_XSS_SAFE_TAGS = frozenset({
    'a', 'abbr', 'acronym', 'address', 'area', 'article', 'aside', 'b', 'base',
    'basefont', 'bdi', 'bdo', 'big', 'blink', 'blockquote', 'br', 'button',
    'caption', 'center', 'cite', 'code', 'col', 'colgroup', 'command', 'content',
    'data', 'datalist', 'dd', 'del', 'detals', 'dfn', 'dialog', 'dir', 'div',
    'dl', 'dt', 'element', 'em', 'fieldset', 'figcaption', 'figure', 'font',
    'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hgroup',
    'hr', 'i', 'image', 'img', 'input', 'ins', 'isindex', 'kbd', 'keygen',
    'label', 'legend', 'li', 'listing', 'main', 'map', 'mark', 'marquee', 'menu',
    'menuitem', 'meter', 'multicol', 'nav', 'nobr', 'noembed', 'noframes',
    'noscript', 'ol', 'optgroup', 'option', 'output', 'p', 'picture', 'plaintext',
    'pre', 'progress', 'q', 'rp', 's', 'samp', 'section', 'select', 'shadow',
    'small', 'spacer', 'span', 'strike', 'strong', 'sub', 'summary', 'sup',
    'table', 'tbody', 'td', 'template', 'textarea', 'tfoot', 'th', 'thead', 'time',
    'tr', 'tt', 'u', 'ul', 'var', 'wbr',
})

# Curated attribute allowlist — tightened from bleach's "allow everything" lambda.
# Per CONTEXT.md: "Tighten allowlists where bleach was overly broad."
_XSS_SAFE_ATTRS = {
    '*': {'class', 'id', 'style', 'title', 'lang', 'dir'},
    'a': {'href', 'target'},
    'img': {'src', 'alt', 'width', 'height'},
    'table': {'border', 'cellpadding', 'cellspacing', 'width', 'summary'},
    'td': {'colspan', 'rowspan', 'align', 'valign'},
    'th': {'colspan', 'rowspan', 'scope', 'align', 'valign'},
    'ol': {'start', 'type'},
    'ul': {'type'},
    'blockquote': {'cite'},
    'col': {'span', 'width'},
    'colgroup': {'span', 'width'},
    'del': {'cite', 'datetime'},
    'ins': {'cite', 'datetime'},
    'time': {'datetime'},
}

# Minimal HTML tags — union of bleach_allowlist markdown_tags and print_tags
_MINIMAL_TAGS = frozenset({
    'a', 'b', 'blockquote', 'br', 'code', 'dd', 'div', 'dt', 'em',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li',
    'ol', 'p', 'pre', 'span', 'strong', 'sub', 'sup', 'table', 'tbody',
    'td', 'tfoot', 'th', 'thead', 'tr', 'tt', 'ul',
})

# Minimal HTML attributes — merged from bleach_allowlist markdown_attrs and
# print_attrs. Note: 'style' from print_attrs is intentionally excluded —
# style values are stripped (tightened from bleach which left empty style="").
_MINIMAL_ATTRS = {
    '*': {'class', 'id'},
    'a': {'href', 'alt', 'title'},
    'img': {'src', 'alt', 'title', 'width', 'height'},
    'td': {'colspan', 'rowspan', 'align', 'valign'},
    'th': {'colspan', 'rowspan', 'scope', 'align', 'valign'},
}


def sanitize(html: str, sanitizer: str) -> str:
    """ Sanitize HTML

    :param html: HTML to be sanitized
    :type html: basestring

    :param sanitizer: name of the sanitizer to use
    :type sanitizer: str

    :result: sanitized HTML
    :rtype: str
    """

    sanitized = get_settings()["kotti.sanitizers"][sanitizer](html)

    return sanitized


def xss_protection_nh3(html: str) -> str:
    """Sanitizer that removes tags not considered XSS safe.

    Uses nh3 with a curated attribute allowlist. Unlike the deprecated
    bleach-based xss_protection(), this does NOT allow all attributes —
    only explicitly listed safe attributes are preserved.

    Script and style tag content is removed entirely (not just the tags).
    Links get rel="noopener noreferrer" for security.

    :param html: HTML to be sanitized
    :type html: str
    :result: sanitized HTML
    :rtype: str
    """
    return nh3.clean(
        html,
        tags=_XSS_SAFE_TAGS,
        attributes=_XSS_SAFE_ATTRS,
        link_rel="noopener noreferrer",
    )


def minimal_html_nh3(html: str) -> str:
    """Sanitizer that only leaves a basic set of tags and attributes.

    Based on markdown and print tag/attribute sets. Style attributes
    are NOT allowed (tightened from bleach which left empty style="").

    :param html: HTML to be sanitized
    :type html: str
    :result: sanitized HTML
    :rtype: str
    """
    return nh3.clean(
        html,
        tags=_MINIMAL_TAGS,
        attributes=_MINIMAL_ATTRS,
        link_rel="noopener noreferrer",
    )


def no_html_nh3(html: str) -> str:
    """Sanitizer that removes **all** tags.

    :param html: HTML to be sanitized
    :type html: str
    :result: plain text
    :rtype: str
    """
    return nh3.clean(html, tags=frozenset(), attributes={})


def xss_protection(html: str) -> str:
    """Deprecated: use xss_protection_nh3 instead.

    .. deprecated::
        xss_protection() is deprecated. Use xss_protection_nh3() instead.
        Will be removed in Kotti 3.0.
    """
    warnings.warn(
        "xss_protection() is deprecated, use xss_protection_nh3() instead. "
        "Will be removed in Kotti 3.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    return xss_protection_nh3(html)


def minimal_html(html: str) -> str:
    """Deprecated: use minimal_html_nh3 instead.

    .. deprecated::
        minimal_html() is deprecated. Use minimal_html_nh3() instead.
        Will be removed in Kotti 3.0.
    """
    warnings.warn(
        "minimal_html() is deprecated, use minimal_html_nh3() instead. "
        "Will be removed in Kotti 3.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    return minimal_html_nh3(html)


def no_html(html: str) -> str:
    """Deprecated: use no_html_nh3 instead.

    .. deprecated::
        no_html() is deprecated. Use no_html_nh3() instead.
        Will be removed in Kotti 3.0.
    """
    warnings.warn(
        "no_html() is deprecated, use no_html_nh3() instead. "
        "Will be removed in Kotti 3.0.",
        DeprecationWarning,
        stacklevel=2,
    )
    return no_html_nh3(html)


def _setup_sanitizers(settings: Dict[str, Union[str, bool]]) -> None:

    # step 1: resolve sanitizer functions and make ``kotti.sanitizers`` a
    # dictionary containing resolved functions

    if not isinstance(settings["kotti.sanitizers"], str):
        return

    sanitizers = {}

    for s in settings["kotti.sanitizers"].split():
        name, dottedname = s.split(":")
        sanitizers[name.strip()] = DottedNameResolver().resolve(dottedname)

    settings["kotti.sanitizers"] = sanitizers


def _setup_listeners(settings):

    # step 2: setup listeners

    for s in settings["kotti.sanitize_on_write"].split():
        dotted, sanitizers = s.split(":")

        classname, attributename = dotted.rsplit(".", 1)
        _class = DottedNameResolver().resolve(classname)

        def _create_handler(attributename, sanitizers):
            def handler(event):
                value = getattr(event.object, attributename)
                if value is None:
                    return
                for sanitizer_name in sanitizers.split(","):
                    value = settings["kotti.sanitizers"][sanitizer_name](value)
                setattr(event.object, attributename, value)

            return handler

        objectevent_listeners[(ObjectInsert, _class)].append(
            _create_handler(attributename, sanitizers)
        )
        objectevent_listeners[(ObjectUpdate, _class)].append(
            _create_handler(attributename, sanitizers)
        )


def includeme(config: Configurator) -> None:
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    _setup_sanitizers(config.registry.settings)
    _setup_listeners(config.registry.settings)
