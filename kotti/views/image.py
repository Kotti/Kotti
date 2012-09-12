# -*- coding: utf-8 -*-

import PIL
from kotti.util import _
from kotti.util import extract_from_settings
from kotti.views.file import AddFileFormView, EditFileFormView
from kotti.resources import Image
from kotti.resources import IImage
from plone.scale.scale import scaleImage
from pyramid.response import Response
from pyramid.view import view_config

PIL.ImageFile.MAXBLOCK = 33554432

# default image scales
image_scales = {
    'span1': [60, 120],
    'span2': [160, 320],
    'span3': [260, 520],
    'span4': [360, 720],
    'span5': [460, 920],
    'span6': [560, 1120],
    'span7': [660, 1320],
    'span8': [760, 1520],
    'span9': [860, 1720],
    'span10': [960, 1920],
    'span11': [1060, 2120],
    'span12': [1160, 2320],
    }


class EditImageFormView(EditFileFormView):

    pass


class AddImageFormView(AddFileFormView):

    item_type = _(u"Image")

    def add(self, **appstruct):

        buf = appstruct['file']['fp'].read()

        return Image(
            title=appstruct['title'],
            description=appstruct['description'],
            tags=appstruct['tags'],
            data=buf,
            filename=appstruct['file']['filename'],
            mimetype=appstruct['file']['mimetype'],
            size=len(buf), )


class ImageView(object):

    def __init__(self, context, request):

        self.context = context
        self.request = request

    @view_config(context=IImage,
                 name='view',
                 permission='view',
                 renderer='kotti:templates/view/image.pt')
    def view(self):
        return {}

    @view_config(context=IImage,
                 name="image",
                 permission='view')
    def image(self, subpath=None):
        """Return the image in a specific scale, either inline
        (default) or as attachment."""

        if subpath is None:
            subpath = self.request.subpath

        width, height = (None, None)
        subpath = list(subpath)

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

        if width and height:
            image, format, size = scaleImage(self.context.data,
                                             width=width,
                                             height=height,
                                             direction="thumb")
        else:
            image = self.context.data

        res = Response(
            headerlist=[('Content-Disposition', '%s;filename="%s"' % (
                disposition,
                self.context.filename.encode('ascii', 'ignore'))),
                ('Content-Length', str(len(image))),
                ('Content-Type', str(self.context.mimetype)),
            ],
            body=image,
            )

        return res


def _load_image_scales(settings):
    image_scale_strings = extract_from_settings(
        'kotti.image_scales.', settings)

    for k in image_scale_strings.keys():
        image_scales[k] = [int(x) for x in image_scale_strings[k].split("x")]


def includeme(config):
    _load_image_scales(config.registry.settings)

    config.scan("kotti.views.image")
    config.add_view(
        AddImageFormView,
        name=Image.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
        )
    config.add_view(
        EditImageFormView,
        context=Image,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
        )
