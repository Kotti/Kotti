.. _images:

Image URLs
==========

Kotti provides on-the-fly image scaling by utilizing `plone.scale`_.

Images can be referenced by this URL schema: ``/path/to/image_content_object/image[/<image_scale>]/download]`` where ``<image_scale>`` is a predefined image scale (see below).

If the last URL path segment is ``download``, the image will be served with ``Content-disposition: attachment`` otherwise it will be served with ``Content-disposition: inline``.

Predefined image scale sizes
----------------------------

You may define image scale sizes in your ``.ini`` file by setting values for ``kotti.image_scales.<scale_name>`` to values of the form ``<max_width>x<max_height>`` (e.g. ``kotti.image_scales.thumb = 160x120`` with the resulting scale name ``thumb``).

``span1`` (60x120) to ``span12`` (1160x2320) are always defined (with values corresponding to the Twitter Bootstrap default grid sizes), but their values can be overwritten by setting ``kotti.image_scales.span<N>``  to different values in your .ini file.


.. _plone.scale: http://packages.python.org/plone.scale/
