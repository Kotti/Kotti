.. _blobs

Working with blob data in Kotti
===============================

Kotti provides a flexible mechanism of storing blob data by with the help of
:app:`filedepot`_ storages. Both ``File`` and ``Image`` store their data in
:class:`depot.fields.sqlalchemy.UploadedFileField` and they will offload their
blob data to the configured depot storage. Working together with
:app:`filedepot` configured storages means it is possible to store blob data in
a variety of ways: filesystem, GridFS, Amazon storage, etc. By default
:app:`Kotti` will store its blob data in the configured SQL database, using
``~kotti.filedepot.DBFileStorage`` storage, but you can configure your own
preferred way of storing your blob data.

Configuring a depot store
-------------------------

While :app:`filedepot` allows storing data in any of the configured
filestorages, at this time there's no mechanism in Kotti to select, at runtime,
the depot where new data will be saved. Instead, :app:`Kotti` will store new
files only in the configured *default* store. If, for example, you add a new
depot and make that the default, you should leave the old depot configured so
that :app:`Kotti` will continue serving files uploaded there.

By default, `Kotti` comes configured with a db-based filestorage.::

    kotti.depot.0.name = dbfiles
    kotti.depot.0.backend = kotti.filedepot.DBFileStorage

The depot configured at position 0 is the default file depot. The minimum
information required to configure a depot are the `name` and `backend`. The
`name` can be any string and it is used by :app:`filedepot` to identify the
depot store for a particular saved file. The `name` should never be changed, as
it will make the saved files unaccessible. 

Any further parameters for a particular backend will be passed as keyword
arguments to the backend class. See this example, in which we store, by
default, files in `/var/local/files/` using the
:class:`depot.io.local.LocalFileStorage`::

    kotti.depot.0.name = localfs
    kotti.depot.0.backend = depot.io.local.LocalFileStorage
    kotti.depot.0.storage_path = /var/local/files
    kotti.depot.1.name = dbfiles
    kotti.depot.1.backend = kotti.filedepot.DBFileStorage

Notice that we kept the `dbfiles` storage, but we moved it to position 1. No
blob data will be saved anymore, but existing files in that storage will
continue to be served from there.

Add a blob field to your model
------------------------------
Adding a blob data attribute to your can be as simple as::

    from depot.fields.sqlalchemy import UploadedFileField
    from kotti.resources import Content

    class Person(Content):
        avatar = UploadedFileField()

While you can directly assign a `bytes` value to the `avatar` column, the
``UploadedFileField`` column type works best when you assign a
:class:``cgi.FieldStorage`` instance as value.::

    from StringIO import StringIO
    from kotti.util import _to_fieldstorage

    content = '...'
    data = {
            'fp': StringIO(content),
            'filename': 'avatar.png', 
            'mimetype': 'image/png',
            'size': len(content),
            }
    person = Person()
    person.avatar = _to_fielstorage(**data)

Note that the ``data`` dictionary described here has the same format as the
deserialized value of a ``deform.widget.FileUploadWidget``. See the
:class:`~kotti.views.edit.content.FileAddForm` and 
:class:`~kotti.views.edit.content.FileEditForm` for a full example
of how to add or edit a model with a blob field.

Reading blob data
-----------------

If you try directly to read data from an `UploadedFileField` you'll get a
:class:`depot.fields.upload.UploadedFile` instance, which offers a
dictionary-like interface to the stored file metadata and direct access to a
stream with the stored file through the ``file`` attribute::

    person = DBSession.query(Person).get(1)
    blob = person.avatar.file.read()

You should never write to the file stream directly. Instead, you should assign
a new value to the ``UploadedFileField`` column, as described in the previous
section.

Downloading blob data
---------------------

Serving blob data is facilitated by the
:class:``~kotti.views.file.UploadedFileResponse``. You should return an
instance of this class as the response of your view, and it will stream the
blob from the storage to the client browser. As parameters it takes the blob
column and the type of disposition: ``inline`` or ``attachment`` (to trigger a
download in the browser). This, for example is the ``inline-view`` view for a
:class:``~kotti.resources.File``::

    @view_config(name='inline-view', context=File, permission='view')
    def inline_view(context, request):
        return UploadedFileResponse(context.data, request, disposition='inline')

If the used depot storage offers a ``public_url`` value for the blob, then
``UploadedFileResponse``, instead of streaming the data, will redirect instead
to that location.

Inheritance issues with UploadedFileField columns
-------------------------------------------------

You should be aware that, presently, inheriting the ``UploadedFileField`` column doesn't work properly. For a solution to this problem, look how we solve the problem using :meth:`~kotti.resources.File.__declare_last__`, which will solve the problem for the :class:`kotti.resources.Image` subclass.

.. _filedepot: https://pypi.python.org/pypi/filedepot/
