from fanstatic import Group, Library, Resource
from js.bootstrap import bootstrap_js
from js.bootstrap import bootstrap_responsive_css
from js.jquery import jquery
from js.jquery_timepicker_addon import timepicker
from js.jqueryui_tagit import tagit
from pkg_resources import resource_filename


# deform doesn't provide fanstatic resources itself
deform_dir = resource_filename("deform", "static")
lib_deform = Library("deform", deform_dir)
deform_js = Resource(lib_deform, "scripts/deform.js")
jquery_form_js = Resource(
    lib_deform,
    "scripts/jquery.form.js",
    depends=[jquery, ])


# deform_bootstrap doesn't provide fanstatic resources itself
# this should be moved to deform_bootstrap in the future
deform_bootstrap_dir = resource_filename("deform_bootstrap", "static")
lib_deform_bootstrap = Library("deform_bootstrap", deform_bootstrap_dir)
deform_bootstrap_js = Resource(
    lib_deform_bootstrap,
    "deform_bootstrap.js",
    depends=[deform_js, ])


# Kotti's resources
lib_kotti = Library("kotti", "static")
kotti_js = Resource(lib_kotti,
    "kotti.js",
    depends=[deform_bootstrap_js, ],
    minified="kotti.min.js",
    bottom=True)
base_css = Resource(lib_kotti,
    "base.css",
    depends=[bootstrap_responsive_css, ],
    minified="base.min.css")
edit_css = Resource(lib_kotti,
    "edit.css",
    depends=[base_css, ],
    minified="edit.min.css")
view_css = Resource(lib_kotti,
    "view.css",
    depends=[base_css, ],
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
            - fanstatic.Resource object
            - fanstatic.Group object"""

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
    view_css, ])
view_needed_js = NeededGroup([
    jquery,
    bootstrap_js, ])
view_needed = NeededGroup([
    view_needed_css,
    view_needed_js, ])

edit_needed_css = NeededGroup([
    edit_css, ])
edit_needed_js = NeededGroup([
    jquery,
    bootstrap_js,
    tagit,
    kotti_js,
    timepicker,
    jquery_form_js,
    deform_bootstrap_js])
edit_needed = NeededGroup([
    edit_needed_css,
    edit_needed_js, ])
