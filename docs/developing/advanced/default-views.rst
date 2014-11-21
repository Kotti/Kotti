.. _default-views:

Default views in Kotti
======================

In Kotti every ``Content`` node has a ``default_view`` attribute.
This allows to have different views for any instance of a
content type without having to append the view name to the URL.

You can also provide additional views for the default content
types in your third party add on.  To make them show up in the
default view selector in the UI you have to append a
``(view_name, view_title)`` tuple to the ``type_info`` attribute
of the respective content class via its class method
``add_selectable_default_view(name, title)``.

E.g. the ``kotti_media`` add on provides a ``media_folder_view``
for the ``Document`` content type that lists all 'media type'
children of a ``Document`` with their title and a media player.

Registration is done like this:

.. code-block:: python

    from kotti.resources import Document
    from kotti_media import _

    def includeme(config):

        Document.type_info.add_selectable_default_view("media_folder_view",
                                                       _("Media Folder"))
