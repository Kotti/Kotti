import colander
from pyramid.threadlocal import get_current_request
from deform.widget import Widget

from kotti.resources import Tag

ADD_VIEWS = [u'add_document', ]


class TagHolder(object):
    """ A type leaving the value untouched.
    """
    def serialize(self, node, value):
        return value

    def deserialize(self, node, value):
        return value


class TagItWidget(Widget):
    template = 'tag_it'

    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (colander.null, None):
            cstruct = ''
        request = get_current_request()
        if request.view_name not in ADD_VIEWS:
            if getattr(request.context, 'tags', None) is not None:
                cstruct = ','.join(request.context.tags)
        template = readonly and self.readonly_template or self.template
        return field.renderer(template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct):
        if pstruct is colander.null:
            return colander.null
        if isinstance(pstruct, basestring):
            return [item.strip() for item in pstruct.split(',') if item]
        return tuple(pstruct)


@colander.deferred
def deferred_tag_it_widget(node, kw):
    all_tags = Tag.query.all()
    available_tags = [tag.title.encode('utf-8') for tag in all_tags]
    widget = TagItWidget(available_tags=available_tags,
                         missing='')
    return widget
