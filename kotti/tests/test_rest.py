from kotti.resources import TypeInfo, Content, Document
from kotti.rest import schema_factory
from kotti.testing import DummyRequest
from sqlalchemy import Column, ForeignKey, Integer
import colander
import json


class Something(Content):
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    type_info = TypeInfo(name="Something")


@schema_factory(Something)
def sa(context, request):
    return 'a'


@schema_factory(Something, name='b')
def sb(context, request):
    return 'b'


class TestSerializer:

    def test_serializes_decorator(self, config):
        from kotti.rest import ISchemaFactory
        from zope.component import getUtility

        config.scan('kotti.tests.test_rest')
        obj, req = Something(), DummyRequest()

        assert getUtility(ISchemaFactory,
                          name='Something/default')(obj, req) == 'a'
        assert getUtility(ISchemaFactory,
                          name='Something/b')(obj, req) == 'b'


# TODO: test content factories


class TestSerializeDefaultContent:

    def make_one(self, config, klass=Content, **kw):
        from kotti.rest import serialize

        config.scan('kotti.rest')

        props = {
            'name': 'doc-a',
            'title': u'Doc A',
            'description': u'desc...'
        }
        props.update(**kw)
        obj = klass(**props)
        return serialize(obj, DummyRequest())

    def test_serialize_content(self, config):
        from kotti.resources import Content
        resp = self.make_one(config, klass=Content)
        assert resp['data']['id'] == u'doc-a'
        assert resp['data']['attributes']['title'] == u'Doc A'
        assert resp['data']['attributes']['description'] == u'desc...'
        assert resp['data']['attributes']['tags'] == colander.null

    def test_serialize_document(self, config):
        resp = self.make_one(config, Document, body=u'Body text')
        assert resp['data']['attributes']['body'] == u'Body text'

    def test_serialize_file(self, config, filedepot):
        from kotti.resources import File
        res = self.make_one(config, File, data='file content')
        assert res  # TODO: finish

    # TODO: serializing an image


class TestRestView:

    def _make_request(self, config, **kw):
        from kotti.rest import ACCEPT
        from webob.acceptparse import MIMEAccept
        from pyramid.request import Request

        _environ = {
            'PATH_INFO': '/',
            'SERVER_NAME': 'example.com',
            'SERVER_PORT': '80',
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'PATCH'
            }
        _environ.update(**kw)

        req = Request(accept=MIMEAccept(ACCEPT), environ=_environ)
        req.registry = config.registry
        return req

    def _get_view(self, context, request, name=''):
        from pyramid.compat import map_
        from pyramid.interfaces import IView
        from pyramid.interfaces import IViewClassifier
        from zope.interface import providedBy

        provides = [IViewClassifier] + map_(
            providedBy,
            (request, context)
        )

        return request.registry.adapters.lookup(provides, IView, name=name)

    def test_get(self, config):
        from kotti.rest import ACCEPT
        from webob.acceptparse import MIMEAccept

        config.include('kotti.rest')

        req = DummyRequest(accept=MIMEAccept(ACCEPT))
        doc = Document()

        view = self._get_view(doc, req)
        data = view(doc, req).json_body

        assert 'attributes' in data['data']
        assert 'meta' in data

    def test_jsonp_as_renderer(self, config):
        from pyramid.renderers import render

        config.include('kotti.rest')

        doc = Document('1')
        req = DummyRequest()

        js = json.loads(render('kotti_jsonp', doc, request=req))
        assert js['data']['attributes']['body'] == "1"

    def test_put(self, config):
        config.include('kotti.rest')
        req = self._make_request(config, REQUEST_METHOD='PUT')
        req.body = json.dumps({
            'data': {
                'type': 'Document',
                'attributes': {
                    'title': u"Title here",
                    'body': u"Body here"
                }
            }
        })
        doc = Document(name='parent')
        view = self._get_view(doc, req)
        data = view(doc, req).json_body['data']

        assert data['attributes']['title'] == u'Title here'
        assert data['id'] == 'title-here'

        assert doc.keys() == ['title-here']

    def test_patch(self, config):

        config.include('kotti.rest')

        doc = Document(name='first',
                       title=u'Title here',
                       description=u"Description here",
                       body=u"body here")

        req = self._make_request(config)
        req.body = json.dumps({
            'data': {
                'id': 'first',
                'type': 'Document',
                'attributes': {
                    'title': u"Title was changed",
                    'body': u"Body was changed"
                }
            }
        })

        view = self._get_view(doc, req)
        data = view(doc, req).json_body

        assert data['data']['attributes']['title'] == u"Title was changed"
        assert data['data']['attributes']['body'] == u"Body was changed"

    def test_post(self, config):

        config.include('kotti.rest')

        doc = Document(name='first',
                       title=u'Title here',
                       description=u"Description here",
                       body=u"body here")

        req = self._make_request(config)
        req.body = json.dumps({
            'data': {
                'id': 'first',
                'type': 'Document',
                'attributes': {
                    'title': u"Title was changed",
                    'body': u"Body was changed"
                }
            }
        })

        view = self._get_view(doc, req)
        data = view(doc, req).json_body

        assert data['data']['attributes']['title'] == u"Title was changed"
        assert data['data']['attributes']['body'] == u"Body was changed"

    # TODO: test delete method
