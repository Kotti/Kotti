import uuid

from mock import patch
from pytest import fixture
from zope.interface import implements

from kotti.interfaces import IBlobStorage


class DummyBlobstore(object):
    """ A dummy blobstore for usage in tests """

    implements(IBlobStorage)
    _data = {}

    def __init__(self, config):
        self.config = config

    def read(self, id):
        return self._data[id]

    def write(self, data):
        id = str(uuid.uuid4())
        self._data[id] = data
        return id

    def delete(self, id):
        try:
            del self._data[id]
        except KeyError:
            return False
        else:
            return True


@fixture
def dummy_blobstore():
    return DummyBlobstore('/dummy/config/')


@fixture
def blobstore_settings(dummy_blobstore):
    return patch(
        'kotti.resources.get_settings',
        return_value={
            'kotti.blobstore': dummy_blobstore})


@fixture
def blobstore_settings_events(dummy_blobstore):
    return patch(
        'kotti.events.get_settings',
        return_value={
            'kotti.blobstore': dummy_blobstore})


def test_file_data_property(dummy_blobstore, blobstore_settings):
    with blobstore_settings:

        from kotti.resources import File

        data = 'Some test data'
        f1 = File()
        f1.data = data
        id = f1._data
        assert type(id) == str
        assert f1.data == data

        f1._delete()
        assert id not in dummy_blobstore._data


def test_blobstore_migration_from(dummy_blobstore, blobstore_settings,
                                  db_session, content, root):
    with blobstore_settings:
        from kotti.resources import File
        from kotti.resources import migrate_blobs
        data = 'Some test data'
        root['f1'] = f1 = File()
        f1._data = data
        db_session.flush()

        f1 = root['f1']
        migrate_blobs(from_db=True)
        assert f1.data == data
        assert type(f1._data) == str
        assert dummy_blobstore._data[f1._data] == data


def test_blobstore_migration_to(dummy_blobstore, blobstore_settings,
                                db_session, content, root):
    with blobstore_settings:
        from kotti.resources import File
        from kotti.resources import migrate_blobs
        root['f1'] = f1 = File()
        data = 'Some test data'
        f1.data = data
        id = f1._data
        assert type(id) == str
        db_session.flush()

        f1 = root['f1']
        migrate_blobs(to_db=True)
        db_session.flush()

        f1 = root['f1']
        assert f1._data == data
        assert id not in dummy_blobstore._data


def test_blobstore_events(dummy_blobstore, blobstore_settings,
                          blobstore_settings_events, db_session,
                          content, root, events):

    with blobstore_settings:
        with blobstore_settings_events:
            from kotti.resources import File
            root['f1'] = f1 = File()
            data = 'Some test data'
            f1.data = data
            id = f1._data
            db_session.flush()

            assert File.query.count() == 1
            assert id in dummy_blobstore._data

            del root['f1']
            db_session.flush()
            assert File.query.count() == 0

            assert id not in dummy_blobstore._data
