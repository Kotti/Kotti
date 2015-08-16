import colander
from kotti.testing import DummyRequest


class TestSerializer:
    from kotti.resources import Content

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
        assert self.make_one(config, klass=Content) == {
            'id': u'doc-a',
            'title': u'Doc A',
            'tags': colander.null,
            'description': u'desc...',
        }

    def test_serialize_document(self, config):
        from kotti.resources import Document

        assert self.make_one(config, Document, body=u'Body text')== {
            'id': u'doc-a',
            'title': u'Doc A',
            'tags': colander.null,
            'description': u'desc...',
            'body': u'Body text',
        }

    def test_serialize_file(self, config, filedepot):
        from kotti.resources import File
        res = self.make_one(config, File, data='file content')
        print res

    # serializing an image
