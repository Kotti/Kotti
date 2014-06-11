from .util import RootOnlyPredicate
from .util import SettingHasValuePredicate


def includeme(config):
    config.add_static_view('static-kotti', 'kotti:static')

    # deform stuff
    # config.include('deform_bootstrap')
    config.include('pyramid_deform')
    config.include('js.deform')
    # config.include('js.deform_bootstrap')

    # disable deform CSS autoneeding
    # from js.deform import resource_mapping
    # from js.deform import deform_js
    # resource_mapping['deform'] = deform_js

    config.add_view_predicate(
        'root_only', RootOnlyPredicate)
    config.add_view_predicate(
        'if_setting_has_value', SettingHasValuePredicate)
