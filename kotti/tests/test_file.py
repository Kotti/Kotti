from unittest import TestCase
from StringIO import StringIO

from colander import null
from mock import MagicMock
from mock import patch

from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase

class TestFileViews(UnitTestBase):
    def setUp(self):
        from kotti.resources import File
        self.file = File("file contents", "myfile.png", "image/png", 46578)

    def test_inline_view(self):
        from kotti.views.file import inline_view
        res = inline_view(self.file, None)
        headers = res.headers

        assert headers["Content-Disposition"] == 'inline;filename="myfile.png"'
        assert headers["Content-Length"] == 46578
        assert headers["Content-Type"] == "image/png"
        assert res.app_iter == 'file contents'
        
    def test_attachment_view(self):
        from kotti.views.file import attachment_view
        res = attachment_view(self.file, None)
        headers = res.headers

        assert headers["Content-Disposition"] == (
            'attachment;filename="myfile.png"')
        assert headers["Content-Length"] == 46578
        assert headers["Content-Type"] == "image/png"
        assert res.app_iter == 'file contents'

class TestEditFileFormView(TestCase):
    def make_one(self):
        from kotti.views.file import EditFileFormView
        return EditFileFormView(MagicMock(), DummyRequest())

    def test_edit_with_file(self):
        view = self.make_one()
        view.edit(
            title=u'A title', description=u'A description',
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

    def test_edit_without_file(self):
        view = self.make_one()
        view.context.data = 'filecontents'
        view.context.filename = u'myfile.png'
        view.context.mimetype = u'image/png'
        view.context.size = 777
        view.edit(title=u'A title', description=u'A description', file=null)

        assert view.context.title == u'A title'
        assert view.context.description == u'A description'
        assert view.context.data == 'filecontents'
        assert view.context.filename == u'myfile.png'
        assert view.context.mimetype == u'image/png'
        assert view.context.size == 777

class TestAddFileFormView(TestCase):
    def make_one(self):
        from kotti.views.file import AddFileFormView
        return AddFileFormView(MagicMock(), DummyRequest())

    def test_add(self):
        view = self.make_one()
        file = view.add(
            title=u'A title', description=u'A description',
            file=dict(
                fp=StringIO('filecontents'),
                filename=u'myfile.png',
                mimetype=u'image/png',
                ),
            )

        assert file.title == u'A title'
        assert file.description == u'A description'
        assert file.data == 'filecontents'
        assert file.filename == u'myfile.png'
        assert file.mimetype == u'image/png'
        assert file.size == len('filecontents')

    @patch('kotti.views.file.AddFormView.save_success')
    def test_save_success_title_default(self, save_success):
        view = self.make_one()
        appstruct = dict(
            title=u'', description=u'A description',
            file=dict(
                fp=StringIO('filecontents'),
                filename=u'myfile.png',
                mimetype=u'image/png',
                ),
            )
        view.save_success(appstruct)
        save_success.assert_called_with(dict(
            title=u'myfile.png', description=u'A description',
            file=dict(
                fp=appstruct['file']['fp'],
                filename=u'myfile.png',
                mimetype=u'image/png',
                ),
            ))

class TestFileUploadTempStore(TestCase):
    def make_one(self):
        from kotti.views.file import FileUploadTempStore
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
