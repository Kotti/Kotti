"""
Form related base views from which you can inherit.

Inheritance Diagram
-------------------

.. inheritance-diagram:: kotti.views.form
"""

from StringIO import StringIO
from UserDict import DictMixin

import colander
import deform
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid_deform import CSRFSchema
from pyramid_deform import FormView

from kotti import get_settings
from kotti.fanstatic import tagit
from kotti.resources import Tag
from kotti.util import _
from kotti.util import title_to_name
from kotti.util import translate


def get_appstruct(context, schema):
    appstruct = {}
    for field in schema.children:
        if hasattr(context, field.name):
            val = getattr(context, field.name)
            if val is None:
                val = colander.null
            appstruct[field.name] = val
    return appstruct


class ObjectType(colander.SchemaType):
    """ A type leaving the value untouched.
    """
    def serialize(self, node, value):
        return value

    def deserialize(self, node, value):
        return value


@colander.deferred
def deferred_tag_it_widget(node, kw):
    tagit.need()
    all_tags = Tag.query.all()
    available_tags = [tag.title.encode('utf-8') for tag in all_tags]
    widget = CommaSeparatedListWidget(template='tag_it',
                                      available_tags=available_tags)
    return widget


class Form(deform.Form):
    """
    A deform Form that allows 'appstruct' to be set on the instance.
    """

    def render(self, appstruct=None, readonly=False):
        if appstruct is None:
            appstruct = getattr(self, 'appstruct', colander.null)
        return super(Form, self).render(appstruct, readonly=readonly)


class BaseFormView(FormView):
    """
    A basic view for forms with save and cancel buttons.
    """

    form_class = Form
    buttons = (
        deform.Button('save', _(u'Save')),
        deform.Button('cancel', _(u'Cancel')))
    success_message = _(u"Your changes have been saved.")
    success_url = None
    schema_factory = None
    use_csrf_token = True
    add_template_vars = ()

    def __init__(self, context, request, **kwargs):
        self.context = context
        self.request = request
        self.__dict__.update(kwargs)

    def __call__(self):
        if self.schema_factory is not None:
            self.schema = self.schema_factory()
        if self.use_csrf_token and 'csrf_token' not in self.schema:
            self.schema.children.append(CSRFSchema()['csrf_token'])
        result = super(BaseFormView, self).__call__()
        if isinstance(result, dict):
            result.update(self.more_template_vars())
        return result

    def cancel_success(self, appstruct):
        location = self.request.resource_url(self.context)
        return HTTPFound(location=location)
    cancel_failure = cancel_success

    def more_template_vars(self):
        result = {}
        for name in self.add_template_vars:
            result[name] = getattr(self, name)
        return result


class EditFormView(BaseFormView):
    """
    A base form for content editing purposes.

    Set `self.schema_factory` to the context's schema.  Values of
    fields in this schema will be set as attributes on the context.
    An example::

        import colander
        from deform.widget import RichTextWidget

        from kotti.edit.content import ContentSchema
        from kotti.edit.content import EditFormView

        class DocumentSchema(ContentSchema):
            body = colander.SchemaNode(
                colander.String(),
                title=u'Body',
                widget=RichTextWidget(),
                missing=u'',
                )

        class DocumentEditForm(EditFormView):
            schema_factory = DocumentSchema
    """

    add_template_vars = ('first_heading',)

    def before(self, form):
        form.appstruct = get_appstruct(self.context, self.schema)

    def save_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        self.edit(**appstruct)
        self.request.session.flash(self.success_message, 'success')
        location = self.success_url or self.request.resource_url(self.context)
        return HTTPFound(location=location)

    def edit(self, **appstruct):
        for key, value in appstruct.items():
            setattr(self.context, key, value)

    @reify
    def first_heading(self):
        return _(u'Edit ${title}',
                 mapping=dict(title=self.context.title)
                 )


class AddFormView(BaseFormView):
    """
    A base form for content adding purposes.

    Set `self.schema_factory` as with EditFormView.  Also set
    `item_type` to your model class.  An example::

        class DocumentAddForm(AddFormView):
            schema_factory = DocumentSchema
            add = Document
            item_type = u'Document'
    """

    success_message = _(u"Item was added.")
    item_type = None
    add_template_vars = ('first_heading',)

    def save_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        name = self.find_name(appstruct)
        new_item = self.context[name] = self.add(**appstruct)
        self.request.session.flash(self.success_message, 'success')
        location = self.success_url or self.request.resource_url(new_item)
        return HTTPFound(location=location)

    def find_name(self, appstruct):
        name = appstruct.get('name')
        if name is None:
            name = title_to_name(
                appstruct['title'], blacklist=self.context.keys())
        return name

    @reify
    def first_heading(self):
        context_title = getattr(self.request.context, 'title', None)
        type_title = self.item_type or self.add.type_info.title
        if context_title:
            return _(u'Add ${type} to ${title}.',
                     mapping=dict(type=translate(type_title),
                                  title=context_title))
        else:
            return _(u'Add ${type}.', mapping=dict(type=translate(type_title)))


class CommaSeparatedListWidget(deform.widget.Widget):
    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (colander.null, None):
            cstruct = []
        return field.renderer(self.template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct):
        if pstruct is colander.null:
            return colander.null
        return [item.strip() for item in pstruct.split(',') if item]


class FileUploadTempStore(DictMixin):
    """
    A temporary storage for file file uploads

    File uploads are stored in the session so that you don't need
    to upload your file again if validation of another schema node
    fails.
    """

    def __init__(self, request):
        self.session = request.session

    def keys(self):
        return [k for k in self.session.keys() if not k.startswith('_')]

    def __setitem__(self, name, value):
        value = value.copy()
        fp = value.pop('fp')
        value['file_contents'] = fp.read()
        fp.seek(0)
        self.session[name] = value

    def __getitem__(self, name):
        value = self.session[name].copy()
        value['fp'] = StringIO(value.pop('file_contents'))
        return value

    def __delitem__(self, name):
        del self.session[name]

    def preview_url(self, name):
        return None


def validate_file_size_limit(node, value):
    """
    File size limit validator.

    You can configure the maximum size by setting the kotti.max_file_size
    option to the maximum number of bytes that you want to allow.
    """

    value['fp'].seek(0, 2)
    size = value['fp'].tell()
    value['fp'].seek(0)
    max_size = get_settings()['kotti.max_file_size']
    if size > int(max_size) * 1024 * 1024:
        msg = _('Maximum file size: ${size}MB', mapping={'size': max_size})
        raise colander.Invalid(node, msg)
