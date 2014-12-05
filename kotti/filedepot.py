from datetime import datetime
from depot.io.interfaces import StoredFile, FileStorage

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy.orm import deferred

from kotti import Base
from kotti import DBSession

import uuid


class CooperativeMeta(type):
    def __new__(cls, name, bases, members):
        # collect up the metaclasses
        metas = [type(base) for base in bases]

        # prune repeated or conflicting entries
        metas = [meta for index, meta in enumerate(metas)
            if not [later for later in metas[index + 1:]
                if issubclass(later, meta)]]

        # whip up the actual combined meta class derive off all of these
        meta = type(name, tuple(metas), dict(combined_metas=metas))

        # make the actual object
        return meta(name, bases, members)

    def __init__(self, name, bases, members):
        for meta in self.combined_metas:
            meta.__init__(self, name, bases, members)


class DBStoredFile(Base, StoredFile):
    """depotfile StoredFile implementation that stores data in the db.

    Can be used together with DBFileStorage to implement blobs (large files)
    storage in the database.
    """

    __tablename__ = "blobs"
    __metaclass__ = CooperativeMeta

    #: Primary key column in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(Integer(), primary_key=True)
    #: Unique id given to this blob
    #: (:class:`sqlalchemy.types.String`)
    file_id = Column(String(36), index=True)
    #: The original filename it had when it was uploaded.
    #: (:class:`sqlalchemy.types.String`)
    filename = Column(Unicode(100))
    #: MIME type of the blob
    #: (:class:`sqlalchemy.types.String`)
    content_type = Column(String(30))
    #: Size of the blob in bytes
    #: (:class:`sqlalchemy.types.Integer`)
    content_length = Column(Integer())
    #: Date / time the blob was created
    #: (:class:`sqlalchemy.types.DateTime`)
    last_modified = Column(DateTime())
    #: The binary data itself
    #: (:class:`sqlalchemy.types.LargeBinary`)
    data = deferred(Column('data', LargeBinary()))

    def read(self, n=-1):  # pragma: no cover
        """Reads ``n`` bytes from the file.

        If ``n`` is not specified or is ``-1`` the whole
        file content is read in memory and returned
        """
        return

    def close(self, *args, **kwargs):  # pragma: no cover
        """Closes the file.

        After closing the file it won't be possible to read
        from it anymore. Some implementation might not do anything
        when closing the file, but they still are required to prevent
        further reads from a closed file.
        """
        return

    def closed(self):  # pragma: no cover
        """Returns if the file has been closed.

        When ``closed`` return ``True`` it won't be possible
        to read anoymore from this file.
        """
        return


class DBFileStorage(FileStorage):
    """ depotfile FileStorage implementation, uses DBStoredFile to store data
    """

    def get(self, file_id):
        """Returns the file given by the file_id
        """

        f = DBSession.query(DBStoredFile).filter_by(file_id=file_id).first()
        if f is None:
            raise IOError
        return f

    def create(self, content, filename=None, content_type=None):
        """Saves a new file and returns the file id

        ``content`` parameter can either be ``bytes``, another ``file object``
        or a :class:`cgi.FieldStorage`. When ``filename`` and ``content_type``
        parameters are not provided they are deducted from the content itself.
        """
        new_file_id = str(uuid.uuid1())
        content, filename, content_type = self.fileinfo(
            content, filename, content_type)
        if hasattr(content, 'read'):
            content = content.read()

        fstore = DBStoredFile(data=content,
                              file_id=new_file_id,
                              filename=filename,
                              content_type=content_type,
                              content_length=len(content),
                              last_modified=datetime.now())
        DBSession.add(fstore)
        return new_file_id

    def replace(self, file_or_id, content, filename=None, content_type=None):  # pragma: no cover
        """Replaces an existing file, an ``IOError`` is raised if the file didn't already exist.

        Given a :class:`StoredFile` or its ID it will replace the current content
        with the provided ``content`` value. If ``filename`` and ``content_type`` are
        provided or can be deducted by the ``content`` itself they will also replace
        the previous values, otherwise the current values are kept.
        """

        if isinstance(file_or_id, StoredFile):
            file_id = file_or_id.file_id
        else:
            file_id = file_or_id

        content, filename, content_type = self.fileinfo(
            content, filename, content_type)

        fstore = self.get(file_id)

        if filename is not None:
            fstore.filename = filename
        if content_type is not None:
            fstore.content_type = content_type

        if hasattr(content, 'read'):
            content = content.read()

        fstore.data = content

    def delete(self, file_or_id):  # pragma: no cover
        """Deletes a file. If the file didn't exist it will just do nothing."""

        if isinstance(file_or_id, StoredFile):
            file_id = file_or_id.file_id
        else:
            file_id = file_or_id
        fstore = self.get(file_id)
        DBSession.delete(fstore)

    def exists(self, file_or_id):  # pragma: no cover
        """Returns if a file or its ID still exist."""
        if isinstance(file_or_id, StoredFile):
            file_id = file_or_id.file_id
        else:
            file_id = file_or_id
        return bool(
            DBSession.query(StoredFile).filter_by(file_id=file_id).count())


def configure_filedepot(settings):
    from kotti.util import flatdotted_to_dict
    from depot.manager import DepotManager

    config = flatdotted_to_dict('kotti.depot.', settings)
    for name, conf in config.items():
        if DepotManager.get(name) is None:
            DepotManager.configure(name, conf, prefix='')


def includeme(config):
    configure_filedepot(config.get_settings())
