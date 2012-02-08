from pkg_resources import resource_filename

from deform import Form
from deform import ZPTRendererFactory
from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request

def translator(term):
    request = get_current_request()
    if request is not None:
        return get_localizer(request).translate(term)
    else:
        return term.interpolate() if hasattr(term, 'interpolate') else term

def includeme(config):
    config.add_static_view('static-deform', 'deform:static')
    config.add_static_view('static-kotti', 'kotti:static')
    config.include('deform_bootstrap')

    deform_templates = resource_filename('deform', 'templates')
    kotti_templates = resource_filename('kotti', 'templates/edit/widgets')
    Form.default_renderer = ZPTRendererFactory(
        (kotti_templates, deform_templates), translator=translator)
