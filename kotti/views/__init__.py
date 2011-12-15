def includeme(config):
    from kotti.resources import IContent

    config.add_static_view('static-deform', 'deform:static')
    config.add_static_view('static-kotti', 'kotti:static')
    config.add_view('kotti.views.view.view_content_default', context=IContent)
    config.add_view(
        'kotti.views.edit.add_node',
        name='add',
        permission='add',
        renderer='kotti:templates/edit/add.pt',
        )
    config.add_view(
        'kotti.views.edit.move_node',
        name='move',
        permission='edit',
        renderer='kotti:templates/edit/move.pt',
        )
