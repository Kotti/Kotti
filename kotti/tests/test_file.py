from StringIO import StringIO
from colander import null

from mock import MagicMock
import pytest

from kotti.testing import DummyRequest


class TestFileViews:
    def _create_file(self, config):
        from kotti.resources import File
        self.file = File("file contents", u"myf\xfcle.png", u"image/png")

    def _test_common_headers(self, headers):
        for name in ('Content-Disposition', 'Content-Length', 'Content-Type'):
            assert type(headers[name]) == str
        assert headers["Content-Length"] == "13"
        assert headers["Content-Type"] == "image/png"

    def test_inline_view(self, config):
        self._create_file(config)
        from kotti.views.file import inline_view
        res = inline_view(self.file, None)
        headers = res.headers

        self._test_common_headers(headers)
        assert headers["Content-Disposition"] == 'inline;filename="myfle.png"'
        assert res.body == 'file contents'

    def test_attachment_view(self, config):
        self._create_file(config)
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

        class MockFileColumn(object):
            def __init__(self):
                self.file = MagicMock()

            def __set__(self, instance, value):
                if isinstance(value, StringIO):
                    value.seek(0)
                    rv = value.read()
                else:
                    rv = value
                self.file.read.return_value = rv

        class MockDepotFile(object):
            data = MockFileColumn()

        return FileEditForm(MockDepotFile(), DummyRequest())

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
        assert view.context.data.file.read() == 'filecontents'
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
        assert view.context.data.file.read() == 'filecontents'
        assert view.context.filename == u'myfile.png'
        assert view.context.mimetype == u'image/png'
        assert view.context.size == 777


class TestFileAddForm:
    def make_one(self):
        from kotti.views.edit.content import FileAddForm
        return FileAddForm(MagicMock(), DummyRequest())

    def test_add(self, config):
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
        assert file.data.file.read() == 'filecontents'
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


class TestDepotStore:

    @classmethod
    def setup_class(cls):
        from depot.manager import DepotManager
        from datetime import datetime

        class TestStorage:
            def __init__(self):
                self._storage = {}
                self._storage.setdefault(0)

            def get(self, id):
                f = MagicMock()
                f.read.return_value = self._storage[id]

                # needed to make JSON serializable, Mock objects are not
                f.last_modified = datetime.now()
                f.filename = str(id)
                f.public_url = ''
                f.content_type = 'image/png'

                return f

            def create(self, content, filename=None, content_type=None):
                id = max(self._storage) + 1
                self._storage[id] = content
                return id

            def delete(self, id):
                del self._storage[int(id)]

        DepotManager._depots = {
            'default': MagicMock(wraps=TestStorage())
        }

    @classmethod
    def teardown_class(cls):
        from depot.manager import DepotManager
        DepotManager._depots = {}

    from kotti.resources import File, Image

    @pytest.mark.parametrize("factory", [File, Image])
    def test_create(self, factory):
        f = factory('file content')
        assert len(f.data['files']) == 1
        assert f.data.file.read() == 'file content'

    @pytest.mark.parametrize("factory", [File, Image])
    def test_edit_content(self, factory):
        f = factory('file content')
        assert f.data.file.read() == 'file content'
        f.data = 'edited'
        assert f.data.file.read() == 'edited'

    @pytest.mark.parametrize("factory", [File, Image])
    def test_session_rollback(self, factory, db_session):
        from depot.manager import DepotManager

        f = factory(data='file content', name=u'content', title=u'content')
        id = f.data['file_id']

        assert id in DepotManager.get()._storage.keys()

        db_session.add(f)
        db_session.flush()
        assert id in DepotManager.get()._storage.keys()
        db_session.rollback()
        assert id not in DepotManager.get()._storage.keys()
        assert DepotManager.get().delete.called

    @pytest.mark.parametrize("factory", [File, Image])
    def test_delete(self, factory, db_session, root):
        from depot.manager import DepotManager

        f = factory(data='file content', name=u'content', title=u'content')
        id = f.data['file_id']
        root[str(id)] = f
        db_session.flush()

        assert id in DepotManager.get()._storage.keys()

        del root[str(id)]
        import transaction; transaction.commit()

        assert DepotManager.get().delete.called
        assert id not in DepotManager.get()._storage.keys()
