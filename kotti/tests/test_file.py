from StringIO import StringIO

from colander import null
from mock import MagicMock

from kotti.testing import DummyRequest


class TestFileViews:
    def setup_method(self, method):
        from kotti.resources import File
        self.file = File("file contents", u"myf\xfcle.png", u"image/png")

    def _test_common_headers(self, headers):
        for name in ('Content-Disposition', 'Content-Length', 'Content-Type'):
            assert type(headers[name]) == str
        assert headers["Content-Length"] == "13"
        assert headers["Content-Type"] == "image/png"

    def test_inline_view(self):
        from kotti.views.file import inline_view
        res = inline_view(self.file, None)
        headers = res.headers

        self._test_common_headers(headers)
        assert headers["Content-Disposition"] == 'inline;filename="myfle.png"'
        assert res.body == 'file contents'

    def test_attachment_view(self):
        from kotti.views.file import attachment_view
        res = attachment_view(self.file, None)
        headers = res.headers

        self._test_common_headers(headers)
        assert headers["Content-Disposition"] == (
            'attachment;filename="myfle.png"')
        assert res.body == 'file contents'


class TestFileEditForm:
    def make_one(self):
        from kotti.views.edit.content import FileEditForm
        return FileEditForm(MagicMock(), DummyRequest())

    def test_edit_with_file(self):
        view = self.make_one()
        view.edit(
            title=u'A title', description=u'A description',
            tags=[u"A tag"],
            file=dict(
                fp=StringIO('filecontents'),
                filename=u'myfile.png',
                mimetype=u'image/png',
                ),
            )
        assert view.context.title == u'A title'
        assert view.context.description == u'A description'
        assert view.context.data == 'filecontents'
        assert view.context.filename == u'myfile.png'
        assert view.context.mimetype == u'image/png'
        assert view.context.size == len('filecontents')
        assert view.context.tags == [u"A tag"]

    def test_edit_without_file(self):
        view = self.make_one()
        view.context.data = 'filecontents'
        view.context.filename = u'myfile.png'
        view.context.mimetype = u'image/png'
        view.context.size = 777
        view.edit(title=u'A title',
                  description=u'A description',
                  tags=[],
                  file=null)
        assert view.context.title == u'A title'
        assert view.context.description == u'A description'
        assert view.context.data == 'filecontents'
        assert view.context.filename == u'myfile.png'
        assert view.context.mimetype == u'image/png'
        assert view.context.size == 777


class TestFileAddForm:
    def make_one(self):
        from kotti.views.edit.content import FileAddForm
        return FileAddForm(MagicMock(), DummyRequest())

    def test_add(self):
        view = self.make_one()
        file = view.add(
            title=u'A title',
            description=u'A description',
            tags=[],
            file=dict(
                fp=StringIO('filecontents'),
                filename=u'myfile.png',
                mimetype=u'image/png',
                ),
            )

        assert file.title == u'A title'
        assert file.description == u'A description'
        assert file.tags == []
        assert file.data == 'filecontents'
        assert file.filename == u'myfile.png'
        assert file.mimetype == u'image/png'
        assert file.size == len('filecontents')


class TestFileUploadTempStore:
    def make_one(self):
        from kotti.views.form import FileUploadTempStore
        return FileUploadTempStore(DummyRequest())

    def test_keys(self):
        tmpstore = self.make_one()
        tmpstore.session['important'] = 3
        tmpstore.session['_secret'] = 4
        assert tmpstore.keys() == ['important']

    def test_delitem(self):
        tmpstore = self.make_one()
        tmpstore.session['important'] = 3
        del tmpstore['important']
        assert 'important' not in tmpstore.session
