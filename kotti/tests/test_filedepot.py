import datetime
import pytest

from kotti.filedepot import DBFileStorage, DBStoredFile


class TestDBStoredFile:

    def test_storedfile_interface(self, db_session, events, setup_app):
        f = DBStoredFile('fileid', filename=u'f.jpg', content_type='image/jpeg',
                         content_length=1000, data='content')

        assert f.close() is None
        assert f.closed() is False
        assert f.seekable() is True
        assert f.writable() is False

        assert f.read() == 'content'
        assert f.read() == ''
        f.seek(0)
        assert f.read() == 'content'
        f.seek(0)
        assert f.read(-1) == 'content'
        f.seek(0)
        assert f.read(2) == 'co'
        assert f.read(4) == 'nten'
        assert f.tell() == 6
        f.seek(0)
        f.seek(100)
        assert f.tell() == 100
        assert f.read() == ''

        assert f.content_length == 1000
        assert f.content_type == 'image/jpeg'
        assert f.file_id == 'fileid'
        assert f.filename == u'f.jpg'
        assert f.name == u"f.jpg"
        assert f.public_url is None

        f.data = None
        db_session.add(f)
        db_session.flush()
        assert f.content_length == 0

    def test_content_length(self, db_session, events, setup_app):
        f = DBStoredFile('fileid', data="content")
        db_session.add(f)
        db_session.flush()

        assert f.content_length == 7

        f.data = 'content changed'
        db_session.flush()

        assert f.content_length == len('content changed')

    def test_last_modified(self, monkeypatch, db_session, events, setup_app):
        from kotti import filedepot

        now = datetime.datetime.now()

        class mockdatetime:
            @staticmethod
            def now():
                return now

        monkeypatch.setattr(filedepot, 'datetime', mockdatetime)

        f = DBStoredFile('fileid', data="content")
        db_session.add(f)
        db_session.flush()

        assert f.last_modified == now

        f.last_modified = None
        f.data = 'content changed'
        db_session.flush()

        assert f.last_modified == now


class TestDBFileStorage:

    def make_one(self,
                 content='content here',
                 filename=u'f.jpg',
                 content_type='image/jpg'):

        file_id = DBFileStorage().create(
            content=content, filename=filename, content_type=content_type)
        return file_id

    def test_create(self, db_session):
        file_id = self.make_one()
        assert len(file_id) == 36

        fs = db_session.query(DBStoredFile).filter_by(file_id=file_id).one()
        assert fs.data == "content here"

    def test_get(self, db_session):
        with pytest.raises(IOError):
            DBFileStorage().get("1")

        file_id = self.make_one()
        assert DBFileStorage().get(file_id).data == "content here"

    def test_delete(self, db_session):
        file_id = DBFileStorage().create('content here', u'f.jpg', 'image/jpg')
        fs = DBFileStorage().get(file_id)

        db_session.add(fs)
        db_session.flush()

        assert db_session.query(DBStoredFile.file_id).one()[0] == file_id

        DBFileStorage().delete(file_id)
        assert db_session.query(DBStoredFile).count() == 0

    def test_replace(self, db_session):
        file_id = self.make_one()

        DBFileStorage().replace(file_id, 'second content', u'f2.jpg', 'doc')
        fs = DBFileStorage().get(file_id)
        assert fs.filename == u'f2.jpg'
        assert fs.content_type == 'doc'
        assert fs.read() == 'second content'

        DBFileStorage().replace(fs, 'third content', u'f3.jpg', 'xls')
        assert fs.filename == u'f3.jpg'
        assert fs.content_type == 'xls'
        assert fs.read() == 'third content'
