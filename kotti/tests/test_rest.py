from kotti.resources import TypeInfo, Content, Document
from kotti.rest import restify
from kotti.testing import DummyRequest
from pyramid.exceptions import Forbidden
from pytest import raises
from sqlalchemy import Column, ForeignKey, Integer
import colander
import json
import pytest


class Something(Content):
    id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
    type_info = TypeInfo(name="Something")


@restify(Something)
def sa(context, request):
    return 'a'


@restify(Something, name='b')
def sb(context, request):
    return 'b'


class TestRestify:

    def test_restify_decorator(self, config):
        from kotti.rest import ISchemaFactory
        from zope.component import getUtility

        config.scan('kotti.tests.test_rest')
        obj, req = Something(), DummyRequest()

        assert getUtility(ISchemaFactory,
                          name='Something/default')(obj, req) == 'a'
        assert getUtility(ISchemaFactory,
                          name='Something/b')(obj, req) == 'b'

    def test_get_content_factory(self, config):
        from kotti.rest import get_content_factory
        config.scan('kotti.tests.test_rest')
        assert get_content_factory(DummyRequest(), 'Something') is Something

    def test_IContentFactory_registration(self, config):
        from kotti.rest import IContentFactory
        from zope.component import getUtility

        config.scan('kotti.tests.test_rest')
        assert getUtility(IContentFactory, name='Something') is Something


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


class TestKottiJsonpRenderer:

    def test_jsonp_as_renderer(self, config):
        from pyramid.renderers import render

        config.include('kotti.rest')

        doc = Document('1')
        req = DummyRequest()

        js = json.loads(render('kotti_jsonp', doc, request=req))
        assert js['data']['attributes']['body'] == "1"


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
            'REQUEST_METHOD': 'GET'
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

        config.include('kotti.rest')

        req = self._make_request(config)
        doc = Document()

        view = self._get_view(doc, req)
        data = view(doc, req).json_body

        assert 'attributes' in data['data']
        assert 'meta' in data

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
        resp = view(doc, req)
        data = resp.json_body['data']

        assert resp.status == '201 Created'
        assert data['attributes']['title'] == u'Title here'
        assert data['id'] == 'title-here'
        assert doc.keys() == ['title-here']

    def test_patch(self, config):

        config.include('kotti.rest')

        doc = Document(name='first',
                       title=u'Title here',
                       description=u"Description here",
                       body=u"body here")

        req = self._make_request(config, REQUEST_METHOD='PATCH')
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

        req = self._make_request(config, REQUEST_METHOD='POST')
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

    def test_delete(self, config, db_session):
        config.include('kotti.rest')

        parent = Document(name="parent")
        child = Document(name='child')
        parent['child'] = child

        req = self._make_request(config, REQUEST_METHOD='DELETE')
        req.body = json.dumps({
            'data': {
                'id': 'child',
                'type': 'Document',
            }
        })

        db_session.add(parent)

        view = self._get_view(child, req)

        assert 'child' in parent.keys()
        resp = view(child, req)
        assert resp.status == '204 No Content'
        assert 'child' not in parent.keys()

    @pytest.mark.parametrize("request_method",
                             ['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
    def test_restviews_permissions(self, request_method, config, db_session):
        config.testing_securitypolicy(permissive=False)
        config.include('kotti.rest')

        doc = Document(name='doc')

        req = self._make_request(config, REQUEST_METHOD=request_method)
        req.body = json.dumps({
            'data': {
                'id': 'doc',
                'type': 'Document',
            }
        })
        view = self._get_view(doc, req)

        with raises(Forbidden):
            view(doc, req)
