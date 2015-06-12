"""User management screens
"""

import re
from urllib import urlencode

import colander
from deform import Button
from deform.widget import AutocompleteInputWidget
from deform.widget import CheckboxChoiceWidget
from deform.widget import CheckedPasswordWidget
from deform.widget import SequenceWidget
from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid_deform import FormView

from kotti.events import UserDeleted
from kotti.events import notify
from kotti.message import email_set_password
from kotti.resources import get_root
from kotti.security import ROLES
from kotti.security import SHARING_ROLES
from kotti.security import USER_MANAGEMENT_ROLES
from kotti.security import get_principals
from kotti.security import list_groups_ext
from kotti.security import list_groups_raw
from kotti.security import map_principals_with_local_roles
from kotti.security import set_groups
from kotti.util import _
from kotti.views.form import AddFormView
from kotti.views.form import EditFormView
from kotti.views.site_setup import CONTROL_PANEL_LINKS
from kotti.views.util import template_api


def roles_form_handler(context, request, available_role_names, groups_lister):
    changed = []

    if 'apply' in request.POST:
        p_to_r = {}
        for name in request.params:
            if name.startswith('orig-role::'):
                # orig-role::* is hidden checkboxes that allow us to
                # see what checkboxes were in the form originally
                token, principal_name, role_name = unicode(name).split(u'::')
                if role_name not in available_role_names:
                    raise Forbidden()
                new_value = bool(request.params.get(
                    u'role::{0}::{1}'.format(principal_name, role_name)))
                if principal_name not in p_to_r:
                    p_to_r[principal_name] = set()
                if new_value:
                    p_to_r[principal_name].add(role_name)

        for principal_name, new_role_names in p_to_r.items():
            # We have to be careful with roles that aren't mutable here:
            orig_role_names = set(
                groups_lister(principal_name, context))
            orig_sharing_role_names = set(
                r for r in orig_role_names if r in available_role_names)
            if new_role_names != orig_sharing_role_names:
                final_role_names = orig_role_names - set(available_role_names)
                final_role_names |= new_role_names
                changed.append((principal_name, context, final_role_names))

        if changed:
            request.session.flash(
                _(u'Your changes have been saved.'), 'success')
        else:
            request.session.flash(_(u'No changes were made.'), 'info')

    return changed


def search_principals(request, context=None, ignore=None, extra=()):
    flash = request.session.flash
    principals = get_principals()

    if ignore is None:
        ignore = set()

    entries = []
    for principal_name in extra:
        if principal_name not in ignore:
            p = principals[principal_name]
            entries.append((p, list_groups_ext(principal_name, context)))
            ignore.add(principal_name)

    if 'search' in request.POST:
        query = u'*{0}*'.format(request.params['query'])
        found = False
        for p in principals.search(name=query, title=query, email=query):
            found = True
            if p.name not in ignore:
                entries.append((p, list_groups_ext(p.name, context)))
        if not found:
            flash(_(u'No users or groups were found.'), 'info')

    return entries


@view_config(name='share', permission='manage',
             renderer='kotti:templates/edit/share.pt')
def share_node(context, request):
    # Allow roles_form_handler to do processing on 'apply':
    changed = roles_form_handler(
        context, request, SHARING_ROLES, list_groups_raw)
    if changed:
        for (principal_name, context, groups) in changed:
            set_groups(principal_name, context, groups)
        return HTTPFound(location=request.url)

    existing = map_principals_with_local_roles(context)

    def with_roles(entry):
        all_groups = entry[1][0]
        return [g for g in all_groups if g.startswith('role:')]

    existing = filter(with_roles, existing)
    seen = set([entry[0].name for entry in existing])

    # Allow search to take place and add some entries:
    entries = existing + search_principals(request, context, ignore=seen)
    available_roles = [ROLES[role_name] for role_name in SHARING_ROLES]

    return {
        'entries': entries,
        'available_roles': available_roles,
        }


def name_pattern_validator(node, value):
    """
      >>> name_pattern_validator(None, u'bob')
      >>> name_pattern_validator(None, u'b ob')
      Traceback (most recent call last):
      Invalid: <unprintable Invalid object>
      >>> name_pattern_validator(None, u'b:ob')
      Traceback (most recent call last):
      Invalid: <unprintable Invalid object>
    """
    valid_pattern = re.compile(r"^[a-zA-Z0-9_\-\.]+$")
    if not valid_pattern.match(value):
        raise colander.Invalid(node, _(u"Invalid value"))


def name_new_validator(node, value):
    if get_principals().get(value.lower()) is not None:
        raise colander.Invalid(
            node, _(u"A user with that name already exists."))


@colander.deferred
def deferred_email_validator(node, kw):
    def raise_invalid_email(node, value):
        raise colander.Invalid(
            node, _(u"A user with that email already exists."))
    request = kw['request']
    if request.POST:
        email = request.params.get('email')
        name = request.params.get('name')
        if not name and request.user:
            name = request.user.name
        if email and name:
            principals = get_principals()
            if any(p for p in principals.search(email=email)
                   if p.name.lower() != name.lower()):
                # verify duplicated email except myself when update info
                return raise_invalid_email


def roleset_validator(node, value):
    oneof = colander.OneOf(USER_MANAGEMENT_ROLES)
    [oneof(node, item) for item in value]


def group_validator(node, value):
    principals = get_principals()
    if principals.get('group:' + value) is None:
        raise colander.Invalid(node, _(u"No such group: ${group}",
                                       mapping=dict(group=value)))


class Groups(colander.SequenceSchema):
    group = colander.SchemaNode(
        colander.String(),
        title=_(u'Group'),
        validator=group_validator,
        missing=None,
        widget=AutocompleteInputWidget(),
        )


class PrincipalBasic(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(), title=_(u'Title'))
    email = colander.SchemaNode(
        colander.String(),
        title=_(u'Email'),
        validator=deferred_email_validator,
    )


class PrincipalFull(PrincipalBasic):
    name = colander.SchemaNode(
        colander.String(),
        title=_(u'Name'),
        validator=colander.All(name_pattern_validator, name_new_validator),
        )
    password = colander.SchemaNode(
        colander.String(),
        title=_(u'Password'),
        validator=colander.Length(min=5),
        missing=None,
        widget=CheckedPasswordWidget(),
        )
    active = colander.SchemaNode(
        colander.Boolean(),
        title=_(u'Active'),
        description=_(u"Untick this to deactivate the account."),
        )
    roles = colander.SchemaNode(
        colander.Set(),
        validator=roleset_validator,
        missing=[],
        title=_(u"Global roles"),
        widget=CheckboxChoiceWidget(),
        )
    groups = Groups(
        title=_(u'Groups'),
        missing=[],
        # XXX min_len doesn't really do what we want here.  We'd like
        # the close buttons to appear nevertheless (maybe the now
        # deprecated render_initial_item did exactly that).
        widget=SequenceWidget(min_len=1),
        )


def principal_schema(base=PrincipalFull()):
    principals = get_principals()
    schema = base.clone()
    has_groups = True
    try:
        schema['groups']
    except KeyError:
        has_groups = False
    if has_groups:
        all_groups = []
        for p in principals.search(name=u'group:*'):
            value = p.name.split(u'group:')[1]
            label = u"{0}, {1}".format(p.title, value)
            all_groups.append(dict(value=value, label=label))
        schema['groups']['group'].widget.values = all_groups
        schema['roles'].widget.values = [
            (n, ROLES[n].title) for n in USER_MANAGEMENT_ROLES]
    return schema


def user_schema(base=PrincipalFull()):
    schema = principal_schema(base)
    has_password = True
    try:
        schema['password']
    except KeyError:
        has_password = False
    if has_password:
        schema['password'].description = _(
            u"Leave this empty and tick the 'Send password registration' "
            u"box below to have the user set their own password.")
    schema['title'].title = _(u"Full name")
    return schema


def group_schema(base=PrincipalFull()):
    schema = principal_schema(base)
    del schema['password']
    schema['email'].missing = None
    return schema


def _massage_groups_in(appstruct):
    """Manipulate appstruct received from form so that it's suitable
    for saving on the Principal.

    What we do for groups is we prefix them with 'group:'.  And the
    'roles' in the form are really groups too, so we add to 'groups'.

    The value in the form is 'name', not 'group:name', so we'll
    need to append that before we save.
    """
    groups = appstruct.get('groups', [])
    all_groups = list(appstruct.get('roles', [])) + [
        u'group:{0}'.format(g) for g in groups if g]
    if 'roles' in appstruct:
        del appstruct['roles']
    appstruct['groups'] = all_groups


def _massage_groups_out(appstruct):
    """Opposite of '_massage_groups_in': remove 'groups:' prefix and
    split 'groups' into 'roles' and 'groups'.
    """
    d = appstruct
    groups = [g.split(u'group:')[1] for g in d.get('groups', u'')
              if g and g.startswith(u'group:')]
    roles = [r for r in d.get('groups', u'') if r and r.startswith(u'role:')]
    d['groups'] = groups
    d['roles'] = roles
    return d


class UserAddFormView(AddFormView):
    item_type = _(u'User')
    form_options = (('formid', 'deform_user_add'), )
    buttons = (Button('add_user', _(u'Add User')),
               Button('cancel', _(u'Cancel')))

    def schema_factory(self):
        schema = user_schema()
        del schema['active']
        schema.add(colander.SchemaNode(
            colander.Boolean(),
            name=u'send_email',
            title=_(u'Send password registration link.'),
            default=True,
            ))
        return schema

    def add_user_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        _massage_groups_in(appstruct)
        name = appstruct['name'] = appstruct['name'].lower()
        appstruct['email'] = appstruct['email'] and appstruct['email'].lower()
        send_email = appstruct.pop('send_email', False)
        get_principals()[name] = appstruct
        if send_email:
            email_set_password(get_principals()[name], self.request)
        self.request.session.flash(
            _(u'${title} was added.',
              mapping=dict(title=appstruct['title'])), 'success')
        location = self.request.url.split('?')[0] + '?' + urlencode(
            {'extra': name})
        return HTTPFound(location=location)


class GroupAddFormView(UserAddFormView):
    item_type = _(u"Group")
    form_options = (('formid', 'deform_group_add'), )
    buttons = (Button('add_group', _(u'Add Group')),
               Button('cancel', _(u'Cancel')))

    def schema_factory(self):
        schema = group_schema()
        del schema['active']
        return schema

    def add_group_success(self, appstruct):
        appstruct['name'] = u'group:{0}'.format(appstruct['name'].lower())
        return self.add_user_success(appstruct)


@view_config(name='setup-users', permission='admin',
             root_only=True,
             renderer='kotti:templates/site-setup/users.pt')
class UsersManage(FormView):

    UserAddFormView = UserAddFormView
    GroupAddFormView = GroupAddFormView

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        api = template_api(self.context, self.request,
                           cp_links=CONTROL_PANEL_LINKS)

        api.page_title = _(u"User Management")

        principals = get_principals()

        def groups_lister(principal_name, context):
            return principals[principal_name].groups

        # Handling the user/roles matrix:
        changed = roles_form_handler(
            self.context, self.request, USER_MANAGEMENT_ROLES, groups_lister)
        if changed:
            changed_names = []
            for (principal_name, context, groups) in changed:
                principal = principals[principal_name]
                principal.groups = list(groups)
                changed_names.append(principal_name)
            location = self.request.url.split('?')[0] + '?' + urlencode(
                {'extra': ','.join(changed_names)})
            return HTTPFound(location=location)

        extra = self.request.params.get('extra') or ()
        if extra:
            extra = extra.split(',')
        search_entries = search_principals(self.request, extra=extra)
        available_roles = [ROLES[role_name]
                           for role_name in USER_MANAGEMENT_ROLES]

        # Add forms:
        user_addform = self.UserAddFormView(self.context, self.request)()
        if self.request.is_response(user_addform):
            return user_addform

        group_addform = self.GroupAddFormView(self.context, self.request)()
        if self.request.is_response(group_addform):
            return group_addform

        if self.request.params.get('add_user'):
            active_tab = 'add_user'
        elif self.request.params.get('add_group'):
            active_tab = 'add_group'
        else:
            active_tab = 'search'
        return {
            'api': api,
            'entries': search_entries,
            'available_roles': available_roles,
            'user_addform': user_addform['form'],
            'group_addform': group_addform['form'],
            'active_tab': active_tab,
        }


class UserEditFormView(EditFormView):
    @property
    def success_url(self):
        return self.request.url

    def schema_factory(self):
        return user_schema(PrincipalBasic())


class UserManageFormView(UserEditFormView):

    buttons = (Button('save', _(u'Save')),
               Button('cancel', _(u'Cancel')),
               Button('delete', _(u'Delete'), css_class='btn btn-danger'))

    def schema_factory(self):
        schema = user_schema()
        del schema['name']
        return schema

    def before(self, form):
        context = self.context.__dict__.copy()
        context['password'] = u''
        form.appstruct = _massage_groups_out(context)

    def save_success(self, appstruct):
        if appstruct.get('password'):
            hashed = get_principals().hash_password(appstruct['password'])
            appstruct['password'] = hashed
        else:
            appstruct.pop('password', None)
        _massage_groups_in(appstruct)
        return super(UserEditFormView, self).save_success(appstruct)

    def cancel_success(self, appstruct):
        self.request.session.flash(_(u'No changes were made.'), 'info')
        location = u'{0}/@@setup-users'.format(self.request.application_url)
        return HTTPFound(location=location)
    cancel_failure = cancel_success

    def delete_success(self, appstruct):
        location = u'{0}/@@delete-user?name={1}'.format(
            self.request.application_url, self.request.params['name'])
        return HTTPFound(location=location)


class GroupManageFormView(UserManageFormView):
    def schema_factory(self):
        schema = group_schema()
        del schema['name']
        del schema['active']
        return schema


@view_config(name='setup-user', permission='admin',
             root_only=True,
             renderer='kotti:templates/site-setup/user.pt')
class UserManage(FormView):

    GroupManageFormView = GroupManageFormView
    UserManageFormView = UserManageFormView

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        user_or_group = self.request.params['name']
        principal = get_principals()[user_or_group]

        is_group = user_or_group.startswith("group:")
        principal_type = _(u"Group") if is_group else _(u"User")

        api = template_api(
            self.context, self.request,
            page_title=_(u"Edit ${principal_type} ${title}",
                         mapping=dict(principal_type=principal_type,
                                      title=self.context.title)),
            cp_links=CONTROL_PANEL_LINKS,
            principal=principal)

        form_view = self.GroupManageFormView if is_group \
            else self.UserManageFormView
        form = form_view(principal, self.request)()
        if self.request.is_response(form):
            return form

        return {
            'api': api,
            'form': form['form'],
            }


@view_config(name='delete-user', permission='admin',
             root_only=True,
             renderer='kotti:templates/site-setup/delete-user.pt')
def user_delete(context, request):
    principals = get_principals()

    if 'name' in request.params and request.params['name']:
        user_or_group = request.params['name']
        principal = principals.search(name=user_or_group).first()
        if principal is None:
            request.session.flash(_(u'User was not found.'), 'error')
        else:
            is_group = user_or_group.startswith("group:")
            principal_type = _(u"Group") if is_group else _(u"User")

            # We already coming from the confirmation page.
            if 'delete' in request.POST:
                principals.__delitem__(principal.name)
                notify(UserDeleted(principal, request))
                request.session.flash(
                    _(u'${principal_type} ${title} was deleted.',
                      mapping=dict(principal_type=principal_type,
                                   title=principal.title)), 'info')
                location = u'{0}/@@setup-users'.format(request.application_url)
                return HTTPFound(location=location)

            api = template_api(
                context, request,
                page_title=_(u"Delete ${principal_type} ${title}",
                             mapping=dict(principal_type=principal_type,
                                          title=principal.title)),
                principal_type=principal_type,
                principal=principal)
            return {'api': api, }
    else:
        request.session.flash(_(u'No name was given.'), 'error')

    return {'api': template_api(context, request), }


class PreferencesFormView(UserEditFormView):

    def cancel_success(self, appstruct):
        location = self.request.resource_url(get_root())
        return HTTPFound(location=location)
    cancel_failure = cancel_success


@view_config(name='prefs', root_only=True,
             renderer='kotti:templates/edit/simpleform.pt')
class Preferences(FormView):

    PreferencesFormView = PreferencesFormView

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        user = self.request.user
        if user is None:
            raise Forbidden()

        api = template_api(self.context, self.request)
        api.page_title = _(u"My preferences - ${title}",
                           mapping=dict(title=api.site_title))

        form = self.PreferencesFormView(user, self.request)()

        if self.request.is_response(form):
            return form

        return {
            'api': api,
            'form': form['form'],
            'macro': api.macro('kotti:templates/site-setup/master.pt'),
            }


def includeme(config):
    config.scan(__name__)
