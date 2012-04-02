import colander
from pyramid.threadlocal import get_current_request
from deform.widget import Widget

from kotti import DBSession
from kotti.resources import Tag

ADD_VIEWS = [u'add_document', ]


class TagItWidget(Widget):
    template = 'tag_it'
    values = ()
    size = 1

    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (colander.null, None):
            cstruct = ()
        template = readonly and self.readonly_template or self.template
        return field.renderer(template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct):
        if pstruct is colander.null:
            return colander.null
        if isinstance(pstruct, basestring):
            return [item for item in pstruct.split(',')]
        return tuple(pstruct)


@colander.deferred
def deferred_tag_it_widget(node, kw):
    request = get_current_request()
    context_tags = []
    if request.view_name not in ADD_VIEWS:
        context_tags = request.context.tags
    available_tags = DBSession.query(Tag).all()
    widget = TagItWidget(values=context_tags,
                         context_tags=context_tags,
                         available_tags=[tag.title.encode('utf-8') for tag in available_tags],
                         missing='')
    return widget
