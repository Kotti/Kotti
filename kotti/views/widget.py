from types import ListType
from pyramid.threadlocal import get_current_request

import colander
from deform.widget import Widget

from kotti import DBSession
from kotti.resources import Tag
from kotti.util import _

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
            return (pstruct,)
        return tuple(pstruct)


@colander.deferred
def deferred_tag_it_widget(node, kw):
    tags = DBSession.query(Tag).all()
    request = get_current_request()
    context_tags = []
    if request.view_name not in ADD_VIEWS:
        context_tags = DBSession.query(Tag).filter(Tag.items.contains(request.context)).all()
    available_tags = DBSession.query(Tag).all()
    tags = tags if type(tags) == ListType else (tags, )
    values = [(tag.id, tag.title) for tag in tags]
    widget = TagItWidget(values=values,
                         context_tags=[tag.title for tag in context_tags],
                         available_tags=[str(tag.title) for tag in available_tags],
                         missing='')
    return widget
