from pyramid.config import Configurator
from pyramid.threadlocal import manager, get_current_registry
from pyramid.view import render_view_to_response
from pyramid.response import Response

from kotti.request import Request
from kotti.resources import Document


class TestRequest:

    def _make_request(self, name):
        environ = {
            'PATH_INFO': '/',
            'SERVER_NAME': 'example.com',
            'SERVER_PORT': '5432',
            'QUERY_STRING': '',
            'wsgi.url_scheme': 'http',
            }

        request = Request(environ)
        request.view_name = name
        registry = get_current_registry()
        request.registry = registry
        manager.clear()
        manager.push({'request':request, 'registry':registry})

        return request

    def test_can_reify(self, root, setup_app):

        registry = setup_app.registry
        config = Configurator(registry,
                              request_factory='kotti.request.Request')
        manager.push({'registry':config.registry})

        config.add_view(lambda context, request:Response('first'),
                        name='view',
                        context=Document)
        config.commit()

        response = render_view_to_response(
            Document(), self._make_request('view1'), name='', secure=False)
        assert response.body == 'first'

        def view2(context, request):
            assert request.req_method == 'has it'
            return Response("second")

        config.add_request_method(lambda req:'has it', 'req_method', reify=True)
        config.add_view(view2, name='view', context=Document)
        config.commit()

        response = render_view_to_response(
            Document(), self._make_request('view2'), name='', secure=False)
        assert response.body == 'second'
