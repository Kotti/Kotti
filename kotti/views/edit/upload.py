# -*- coding: utf-8 -*-

"""
Created on 2013-02-23
"""

import json
from cgi import FieldStorage
from logging import getLogger

from pyramid.response import Response
from pyramid.view import view_defaults
from pyramid.view import view_config

# from kotti import get_settings
from kotti.fanstatic import upload
from kotti.util import title_to_name
from kotti.views.edit.actions import content_type_factories

log = getLogger(__name__)


@view_defaults(name="upload", context="kotti.resources.Content",
               permission="edit")
class UploadView(object):

    def __init__(self, context, request):
        """ Constructor.

        :param context: Container of the nodes that will be created from
                        uploads.
        :type context: :class:`kotti.resources.Content` or descendants.

        :param request: Current request.
        :type request: :class:`kotti.request.Request`
        """

        self.context = context
        self.request = request
        self.factories = content_type_factories(context, request)['factories']

    @view_config(request_method="GET",
                 renderer="kotti:templates/edit/upload.pt")
    def form(self):
        """ The upload form.

        :result: Data that is needed to render the form (such as allowed child
                 types).
        :rtype: dict
        """

        upload.need()

        return {}

    def possible_factories(self, mimetype):
        """ Return a list of factories for content types that are allowed in the
            context *and* for the given mimetype.

            The result is sorted by length of the matching
            ``uploadable_mimetype`` so that the more specific match comes
            before the more generic match.

            E.g.: when requesting the appropriate content types for
                  ``image/png`` the result order will be [Image, File], because
                  Image matches with its uploadable_mimetype ``image/*`` whereas
                  Files matches 'only' with ``*``.  If there was another content
                  type that would deal with PNGs specificly (and therefore had
                  an uploadable_mimetype ``image/png``) that one would be the
                  first, followed by Imgage and File.

        :param mimetype: MIME type
        :type mimetype: str

        :result: List of content factories.
        :rtype: list
        """

        factories = []
        for factory in self.factories:
            match_score = factory.type_info.is_uploadable_mimetype(mimetype)
            if match_score:
                factories.append((match_score, factory))

        return [f[1] for f in sorted(
            factories, key=lambda factory: -factory[0])]

    @view_config(name="content_types", request_method="GET",
                 accept="application/json", renderer="json")
    def content_types(self):
        """ Return a list of content type names and title for those types that
            can be created from files of the MIME type given as GET parameter.

        :result: JSON object with a single attribute ``content_types``.  This
                 is a list objects with name and title attributes.
        :rtype: dict
        """

        mimetype = self.request.GET['mimetype']

        result = {"content_types": [{
            'name': f.type_info.name,
            'title': f.type_info.title,
        } for f in self.possible_factories(mimetype)]}

        return result

    def factory_by_name(self, content_type_name):
        """ Return a factory (i.e. content class) by its name.

        :param content_type_name: type_info.name of the class.
        :type content_type_name: str

        :result: Content factory
        :rtype: :class:`kotti.resources.Content` or subclass thereof.
        """

        for f in self.factories:
            if f.type_info.name == content_type_name:
                return f

        raise KeyError("Content of that type is not allowed in this context.")

    # def upload_constraints(self):

    #     return {
    #         'max_file_size': get_settings()['kotti.max_file_size'],
    #     }

    @view_config(request_method="POST", xhr=True, accept="application/json")
    def process_upload(self):
        """ Process a single upload.  Also see:
            https://github.com/valums/file-uploader/blob/master/server/readme.md

        :result: Status object with URL of the created item (on success) or
                 error message on failure.
        :rtype: dict
        """

        fs = self.request.POST['qqfile']
        # We can fail hard, as somebody is trying to cheat on us if that fails.
        assert isinstance(fs, FieldStorage)

        try:
            factory = self.factory_by_name(self.request.POST['content_type'])
        except KeyError, e:
            result = {
                'success': False,
                'error': e.message,
            }
        else:
            name = title_to_name(fs.filename, blacklist=self.context.keys())
            self.context[name] = node = factory.from_field_storage(fs)
            node.title = fs.filename

            result = {
                "success": True,
                "url": self.request.resource_url(node),
            }

        # FineUploader expects JSON with Content-Type 'text/plain'
        response = Response(json.dumps(result))
        response.content_type = 'text/plain'

        return response


def includeme(config):
    config.scan(__name__)
