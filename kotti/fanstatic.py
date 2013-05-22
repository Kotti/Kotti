# -*- coding: utf-8 -*-

from __future__ import absolute_import

from fanstatic import Group
from fanstatic import Library
from fanstatic import Resource
from js.bootstrap import bootstrap_js
from js.bootstrap import bootstrap_responsive_css
from js.deform_bootstrap import deform_bootstrap_js
from js.html5shiv import html5shiv
from js.jquery import jquery
from js.jquery_form import jquery_form
from js.jquery_tablednd import jquery_tablednd
from js.jqueryui import bootstrap as jqueryui_bootstrap_theme
from js.jqueryui_tagit import tagit as ui_tagit


# This is needed until ``kotti.views.form.deferred_tag_it_widget`` is converted
# to a class with a ``requirements`` attribute (that would be auto_needed by
# ``js.deform[_bootstrap]``).
tagit = Group([ui_tagit, jqueryui_bootstrap_theme])

# Kotti's resources
lib_kotti = Library("kotti", "static")
kotti_js = Resource(lib_kotti,
    "kotti.js",
    depends=[deform_bootstrap_js],
    minified="kotti.min.js",
    bottom=True)
contents_view_js = Resource(lib_kotti,
    "contents.js",
    depends=[kotti_js, jquery_tablednd, ],
    minified="contents.min.js",
    bottom=True)
base_css = Resource(lib_kotti,
    "base.css",
    depends=[bootstrap_responsive_css],
    minified="base.min.css",
    dont_bundle=True)
edit_css = Resource(lib_kotti,
    "edit.css",
    depends=[base_css],
    minified="edit.min.css")
view_css = Resource(lib_kotti,
    "view.css",
    depends=[base_css],
    minified="view.min.css")


class NeededGroup(object):
    """A collection of fanstatic resources that supports
       dynamic appending of resources after initialization"""

    def __init__(self, resources=[]):

        if not isinstance(resources, list):
            raise ValueError("resources must be a list of fanstatic.Resource "
                "and/or fanstatic.Group objects")

        self.resources = []

        for resource in resources:
            self.add(resource)

    def add(self, resource):
        """resource may be a:

            - :class:`fanstatic.Resource` object or
            - :class:`fanstatic.Group` object"""

        if isinstance(resource, self.__class__):
            self.resources = self.resources + resource.resources
        elif isinstance(resource, (Resource, Group)):
            self.resources.append(resource)
        else:
            raise ValueError("resource must be a NeededGroup,"
                "fanstatic.Resource or fanstatic.Group object")

    def need(self):  # pragma: no cover
        # this is tested in fanstatic itself; we should add browser tests
        # for `view_needed` and `edit_needed` (see below)
        Group(self.resources).need()

view_needed_css = NeededGroup([
    view_css,
    ])
view_needed_js = NeededGroup([
    jquery,
    bootstrap_js,
    html5shiv,
    ])
view_needed = NeededGroup([
    view_needed_css,
    view_needed_js,
    ])

edit_needed_css = NeededGroup([
    edit_css,
    jqueryui_bootstrap_theme,
    ])
edit_needed_js = NeededGroup([
    jquery,
    bootstrap_js,
    html5shiv,
    kotti_js,
    jquery_form,
    deform_bootstrap_js,
    ])
edit_needed = NeededGroup([
    edit_needed_css,
    edit_needed_js,
    ])
