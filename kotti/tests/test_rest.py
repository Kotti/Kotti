from kotti.testing import DummyRequest

# from kotti.rest import serializes
# from mock import patch
# from zope.interface import Interface, implements
# import colander
#
#
# class ISomething(Interface):
#     """ dummy """
#
# class Something(object):
#     implements(ISomething)
#
#
# @serializes(ISomething)
# def sa(context, request):
#     return 'a'
#
#
# @serializes(ISomething, name='b')
# def sb(context, request):
#     return 'b'
#
#
# class TestSerializer:
#
#     def test_serializes_decorator(self, config):
#         from kotti.rest import ISerializer
#         from zope.component import getMultiAdapter
#
#         config.scan('kotti.tests.test_rest')
#         obj, req = Something(), DummyRequest()
#
#         assert getMultiAdapter((obj, req), ISerializer, name='b') == 'b'
#         assert getMultiAdapter((obj, req), ISerializer) == 'a'
#
#
# class TestSerializeDefaultContent:
#     from kotti.resources import Content
#
#     def make_one(self, config, klass=Content, **kw):
#         from kotti.rest import serialize
#
#         config.scan('kotti.rest')
#
#         props = {
#             'name': 'doc-a',
#             'title': u'Doc A',
#             'description': u'desc...'
#         }
#         props.update(**kw)
#         obj = klass(**props)
#         return serialize(obj, DummyRequest())
#
#     def test_serialize_content(self, config):
#         from kotti.resources import Content
#         assert self.make_one(config, klass=Content) == {
#             'id': u'doc-a',
#             'title': u'Doc A',
#             'tags': colander.null,
#             'description': u'desc...',
#         }
#
#     def test_serialize_document(self, config):
#         from kotti.resources import Document
#
#         assert self.make_one(config, Document, body=u'Body text')== {
#             'id': u'doc-a',
#             'title': u'Doc A',
#             'tags': colander.null,
#             'description': u'desc...',
#             'body': u'Body text',
#         }
#
#     def test_serialize_file(self, config, filedepot):
#         from kotti.resources import File
#         res = self.make_one(config, File, data='file content')
#         print res
#
#     # TODO: serializing an image
#
#
# class TestRestView:
#     def get_view(self, context, request, name):
#         from pyramid.compat import map_
#         from pyramid.interfaces import IView
#         from pyramid.interfaces import IViewClassifier
#         from zope.interface import providedBy
#
#         provides = [IViewClassifier] + map_(
#             providedBy,
#             (request, context)
#         )
#
#         return request.registry.adapters.lookup(provides, IView, name=name)
#
#     def test_predicate_matching(self, config):
#         from kotti.resources import Document
#         from kotti.rest import ACCEPT
#         from webob.acceptparse import MIMEAccept
#         config.include('kotti.rest')
#
#         req = DummyRequest(accept=MIMEAccept(ACCEPT))
#         doc = Document()
#
#         with patch('kotti.rest.serialize') as serialize:
#             serialize.return_value = 'a'
#             view = self.get_view(doc, req, name='json')
#             resp = view(doc, req)
#             assert resp.json == u'a'


class TestRestView:
    def get_view(self, context, request, name='json'):
        from pyramid.compat import map_
        from pyramid.interfaces import IView
        from pyramid.interfaces import IViewClassifier
        from zope.interface import providedBy

        provides = [IViewClassifier] + map_(
            providedBy,
            (request, context)
        )

        return request.registry.adapters.lookup(provides, IView, name=name)

    def test_predicate_matching(self, config):
        from kotti.resources import Document
        from kotti.rest import ACCEPT
        from webob.acceptparse import MIMEAccept

        config.include('kotti.rest')

        req = DummyRequest(accept=MIMEAccept(ACCEPT))
        doc = Document()

        view = self.get_view(doc, req, name='json')
        resp = view(doc, req)
        assert resp.json

    def test_jsonp_as_renderer(self, config):
        from pyramid.renderers import render
        from kotti.resources import Document

        doc = Document('1')
        config.include('kotti.rest')

        assert render('kotti_jsonp', doc) == '{"body": "1", "tags": null, '\
            '"description": "", "title": ""}'

    def test_jsonp_as_serializer(self, config):
        from kotti.rest import jsonp
        from kotti.resources import Document
        import colander

        config.include('kotti.rest')
        default = jsonp._make_default(DummyRequest())

        doc = Document('1')
        serialized = default(doc)

        assert serialized == {'body': u'1',
                              'tags': colander.null,
                              'description': u'',
                              'title': u''}
