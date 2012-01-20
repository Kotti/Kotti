def includeme(config):
    config.add_static_view('static-deform', 'deform:static')
    config.add_static_view('static-kotti', 'kotti:static')
    config.include('deform_bootstrap')
