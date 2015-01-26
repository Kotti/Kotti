.. _blobs:

Working with blob data in Kotti
===============================

Kotti provides a flexible mechanism of storing blob data by with the help of
`filedepot`_ storages. Both ``File`` and ``Image`` store their data in
:class:`depot.fields.sqlalchemy.UploadedFileField` and they will offload their
blob data to the configured depot storage. Working together with
`filedepot`_ configured storages means it is possible to store blob data in
a variety of ways: filesystem, GridFS, Amazon storage, etc. 

By default Kotti will store its blob data in the configured SQL
database, using :class:`kotti.filedepot.DBFileStorage` storage, but you can
configure your own preferred way of storing your blob data. The benefit of
storing files in ``DBFileStorage`` is having *all* content in a single place
(the DB) which makes backups, exporting and importing of your site's data easy,
as long as you don't have too many or too large files. The downsides of this
approach appear when your database server resides on a different host (network
performance becomes a greater issue) or your DB dumps become too large to be
handled efficiently.

Configuring a depot store
-------------------------

While `filedepot`_ allows storing data in any of the configured
filestorages, at this time there's no mechanism in Kotti to select, at runtime,
the depot where new data will be saved. Instead, Kotti will store new
files only in the configured ``default`` store. If, for example, you add a new
depot and make that the default, you should leave the old depot configured so
that Kotti will continue serving files uploaded there.

By default, Kotti comes configured with a db-based filestorage.::

    kotti.depot.0.name = dbfiles
    kotti.depot.0.backend = kotti.filedepot.DBFileStorage

The depot configured at position 0 is the default file depot. The minimum
information required to configure a depot are the ``name`` and ``backend``. The
``name`` can be any string and it is used by `filedepot`_ to identify the
depot store for a particular saved file. The ``name`` should never be changed, as
it will make the saved files unaccessible.

Any further parameters for a particular backend will be passed as keyword
arguments to the backend class. See this example, in which we store, by
default, files in ``/var/local/files/`` using the
:class:`depot.io.local.LocalFileStorage`::

    kotti.depot.0.name = localfs
    kotti.depot.0.backend = depot.io.local.LocalFileStorage
    kotti.depot.0.storage_path = /var/local/files
    kotti.depot.1.name = dbfiles
    kotti.depot.1.backend = kotti.filedepot.DBFileStorage

Notice that we kept the ``dbfiles`` storage, but we moved it to position 1. No
blob data will be saved there anymore, but existing files in that storage will
continue to be available from there.

Add a blob field to your model
------------------------------
Adding a blob data attribute to your models can be as simple as::

    from depot.fields.sqlalchemy import UploadedFileField
    from kotti.resources import Content

    class Person(Content):
        avatar = UploadedFileField()

While you can directly assign a ``bytes`` value to the ``avatar`` column, the
``UploadedFileField`` column type works best when you assign a
:class:`cgi.FieldStorage` instance as value::

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
    person.avatar = _to_fieldstorage(**data)

Note that the ``data`` dictionary described here has the same format as the
deserialized value of a ``deform.widget.FileUploadWidget``. See
:class:`kotti.views.edit.content.FileAddForm` and 
:class:`kotti.views.edit.content.FileEditForm` for a full example
of how to add or edit a model with a blob field.

Reading blob data
-----------------

If you try directly to read data from an ``UploadedFileField`` you'll get a
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
:class:`kotti.views.file.UploadedFileResponse`. You should return an
instance of this class as the response of your view, and it will stream the
blob from the storage to the client browser. As parameters it takes the blob
column and the type of disposition: ``inline`` or ``attachment`` (to trigger a
download in the browser). This, for example is the ``inline-view`` view for a
:class:`kotti.resources.File`::

    @view_config(name='inline-view', context=File, permission='view')
    def inline_view(context, request):
        return UploadedFileResponse(context.data, request, disposition='inline')

If the used depot storage offers a ``public_url`` value for the blob, then
``UploadedFileResponse``, instead of streaming the data, will redirect to that
location.

Testing UploadedFileField columns
---------------------------------

Because :class:`depot.manager.DepotManager` acts as a singleton, special care
needs to be taken when testing features that involve saving data into
``UploadedFileField`` columns.

``UploadedFileField`` columns require having at least one depot file storage
configured. You can use a fixture called ``filedepot`` to have a mock file
storage available for your tests.

If you're developing new depot file storages you should use the
``no_filedepots`` fixture, which resets the configured depots for the test run
and restores the default depots back, as a teardown.

Inheritance issues with UploadedFileField columns
-------------------------------------------------

You should be aware that, presently, subclassing a model with an
``UploadedFileField`` column doesn't work properly.  As a workaround, add a 
``__declare_last__`` classmethod in your superclass model, similar to the one
below, where we're fixing the ``data`` column of the ``File`` class. ::

    from depot.fields.sqlalchemy import _SQLAMutationTracker

    class File(Content):

        data = UploadedFileField()

        @classmethod
        def __declare_last__(cls):
            event.listen(cls.data, 'set', _SQLAMutationTracker._field_set, retval=True)


Migrating data between two different storages
---------------------------------------------

Kotti provides a script that can migrate blob data from one configured stored
to another and update the saved fields with the new locations. It is not needed
to do this if you just want to add a new torage, or replace the default one,
but you can use it if you'd like to consolidate the blob data in one place
only. You can invoke the script with::

    kotti-migrate-storage <config_uri> --from-storage <name> --to-storage <name>

The storage names are those assigned in the configuration file designated in
``<config_uri>``. For example, let's assume you've started a website that has
the default blob storage, the ``DBFileStorage`` named *dbfiles*. You'd like to
move all the existing blob data to a :class:`depot.io.local.LocalFileStorage`
storage and make that the default. First, add the ``LocalFileStorage`` depot, 
make it the default and place the old ``DBFileStorage`` in position *1*:::

    kotti.depot.0.backend = depot.io.local.LocalFileStorage
    kotti.depot.0.name = localfs
    kotti.depot.0.storage_path = /var/local/files
    kotti.depot.1.backend = kotti.filedepot.DBFileStorage
    kotti.depot.1.name = dbfiles

Now you can invoke the migration with:::

    kotti-migrate-storage <config_uri> --from-storage dbfiles --to-storage localfs

As always when dealing with migrations, make sure you backup your data first!

.. _filedepot: https://pypi.python.org/pypi/filedepot/
