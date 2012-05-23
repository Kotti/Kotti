# -*- coding: utf-8 -*-

import PIL
from kotti.util import _
# from kotti.util import extract_from_settings
from kotti.views.file import AddFileFormView, EditFileFormView
from kotti.resources import Image
from plone.scale.scale import scaleImage
from pyramid.response import Response
from pyramid.view import view_config

PIL.ImageFile.MAXBLOCK = 33554432

# default image scales
image_scales = {
    'thumb': [160, 120],
    'carousel': [560, 420]}


class EditImageFormView(EditFileFormView):

    pass


class AddImageFormView(AddFileFormView):

    item_type = _(u"Image")

    def add(self, **appstruct):

        buf = appstruct['file']['fp'].read()

        return Image(
            title=appstruct['title'],
            description=appstruct['description'],
            data=buf,
            filename=appstruct['file']['filename'],
            mimetype=appstruct['file']['mimetype'],
            size=len(buf), )


class ImageView(object):

    def __init__(self, context, request):

        self.context = context
        self.request = request

    @view_config(context=Image,
                 name='view',
                 permission='view',
                 renderer='kotti:templates/view/image.pt')
    def view(self):
        return {}

    @view_config(context=Image,
                 name="image",
                 permission='view')
    def image(self):
        """return the image in a specific scale, either inline (default) or as attachment"""

        subpath = list(self.request.subpath)

        if (len(subpath) > 0) and (subpath[-1] == "download"):
            disposition = "attachment"
            subpath.pop()
        else:
            disposition = "inline"

        if len(subpath) == 1:
            scale = subpath[0]
            if scale in image_scales:
                # /path/to/image/scale/thumb
                width, height = image_scales[scale]
            else:
                # /path/to/image/scale/160x120
                try:
                    width, height = [int(v) for v in scale.split("x")]
                except ValueError:
                    width, height = (None, None)

        elif len(subpath) == 2:
            # /path/to/image/scale/160/120
            try:
                width, height = [int(v) for v in subpath]
            except ValueError:
                width, height = (None, None)

        else:
            # don't scale at all
            width, height = (None, None)

        if width and height:
            image, format, size = scaleImage(self.context.data,
                                             width=width,
                                             height=height,
                                             direction="thumb")
        else:
            image = self.context.data

        res = Response(
            headerlist=[('Content-Disposition', '%s;filename="%s"' % (disposition,
                                                                      self.context.filename.encode('ascii', 'ignore'))),
                        ('Content-Length', str(len(image))),
                        ('Content-Type', str(self.context.mimetype)), ],
            app_iter=image)

        return res


def includeme(config):
    # TODO: load predefined scales from .ini
    # image_scales = extract_from_settings('kotti.image_scale.', config)

    config.scan("kotti.views.image")
    config.add_view(AddImageFormView,
                    name=Image.type_info.add_view,
                    permission='add',
                    renderer='kotti:templates/edit/node.pt',)
    config.add_view(EditImageFormView,
                    context=Image,
                    name='edit',
                    permission='edit',
                    renderer='kotti:templates/edit/node.pt', )
