def includeme(config):
    config.add_static_view('static-kotti', 'kotti:static')

    # deform stuff
    config.include('pyramid_deform')
    config.include('deform_bootstrap')
