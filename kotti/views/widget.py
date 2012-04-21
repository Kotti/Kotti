import colander
from deform.widget import Widget

from kotti.resources import Tag


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
            cstruct = []
        return field.renderer(self.template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct):
        if pstruct is colander.null:
            return colander.null
        return [item.strip() for item in pstruct.split(',') if item]


@colander.deferred
def deferred_tag_it_widget(node, kw):
    all_tags = Tag.query.all()
    available_tags = [tag.title.encode('utf-8') for tag in all_tags]
    widget = TagItWidget(available_tags=available_tags,
                         missing='')
    return widget
