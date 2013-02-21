def includeme(config):
    config.add_static_view('static-kotti', 'kotti:static')

    # deform stuff
    config.include('deform_bootstrap')
    config.include('pyramid_deform')
    config.include('js.deform')
    config.include('js.deform_bootstrap')

    # disable deform CSS autoneeding
    from js.deform import resource_mapping
    from js.deform import deform_js
    resource_mapping['deform'] = deform_js
