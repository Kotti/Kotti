# -*- coding: utf-8 -*-

"""
Login / logout and forbidden views and forms.
"""

from datetime import datetime

import colander
from deform import Button
from deform import Form
from deform import ValidationFailure
from deform.widget import CheckedPasswordWidget
from deform.widget import HiddenWidget
from formencode.validators import Email
from pyramid.encode import urlencode
from pyramid.httpexceptions import HTTPForbidden
from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget
from pyramid.security import remember
from pyramid.url import resource_url
from pyramid.view import view_config
from pyramid.settings import asbool

from kotti import get_settings
from kotti.message import email_set_password
from kotti.message import validate_token
from kotti.security import get_principals
from kotti.util import _
from kotti.views.util import template_api
from kotti.views.users import deferred_email_validator
from kotti.views.users import name_pattern_validator
from kotti.views.users import name_new_validator
from kotti.views.users import UserAddFormView
from kotti.events import ObjectEvent
from kotti.events import notify


def _find_user(login):
    principals = get_principals()
    principal = principals.get(login)
    if principal is not None:
        return principal
    else:
        try:
            Email().to_python(login)
        except Exception:
            pass
        else:
            for p in principals.search(email=login):
                return p


class UserSelfRegistered(ObjectEvent):
    """ This event is emitted just after user self registered. Intended use
        is to allow addons to do some preparation for such user - create custom
        contents, nodes etc.
        Event handler object parameter is a Principal object
    """


class RegisterSchema(colander.Schema):
    title = colander.SchemaNode(
        colander.String(),
        title=_(u'Full name'))
    name = colander.SchemaNode(
        colander.String(),
        title=_(u'Username'),
        validator=colander.All(name_pattern_validator, name_new_validator)
    )
    email = colander.SchemaNode(
        colander.String(),
        title=_(u'Email'),
        validator=deferred_email_validator,
    )


@view_config(name='register', renderer='kotti:templates/edit/simpleform.pt',
             if_setting_has_value=('kotti.register', True))
def register(context, request):
    schema = RegisterSchema().bind(request=request)
    form = Form(schema, buttons=(Button('register', _(u'Register')),))
    rendered_form = None

    if 'register' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e:
            request.session.flash(_(u"There was an error."), 'error')
            rendered_form = e.render()
        else:
            settings = get_settings()

            appstruct['groups'] = u''
            appstruct['roles'] = u''

            register_groups = settings['kotti.register.group']
            if register_groups:
                appstruct['groups'] = [register_groups]

            register_roles = settings['kotti.register.role']
            if register_roles:
                appstruct['roles'] = set(['role:' + register_roles])

            appstruct['send_email'] = True
            form = UserAddFormView(context, request)
            form.add_user_success(appstruct)
            success_msg = _(
                'Congratulations! You are successfully registered. '
                'You should be receiving an email with a link to set your '
                'password. Doing so will activate your account.'
                )
            request.session.flash(success_msg, 'success')
            name = appstruct['name']
            notify(UserSelfRegistered(get_principals()[name], request))
            return HTTPFound(location=request.application_url)

    if rendered_form is None:
        rendered_form = form.render(request.params)

    api = template_api(
        context, request,
        page_title=_(u"Register - ${title}",
                     mapping=dict(title=context.title)),
    )

    return {
        'api': api,
        'form': rendered_form,
        }


@view_config(name='login', renderer='kotti:templates/login.pt')
def login(context, request):
    """
    Login view.  Renders either the login or password forgot form templates or
    handles their form submission and redirects to came_from on success.

    :result: Either a redirect response or a dictionary passed to the template
             for rendering
    :rtype: pyramid.httpexceptions.HTTPFound or dict
    """

    principals = get_principals()

    came_from = request.params.get(
        'came_from', request.resource_url(context))
    login, password = u'', u''

    if 'submit' in request.POST:
        login = request.params['login'].lower()
        password = request.params['password']
        user = _find_user(login)

        if (user is not None and user.active and
                principals.validate_password(password, user.password)):
            headers = remember(request, user.name)
            request.session.flash(
                _(u"Welcome, ${user}!",
                  mapping=dict(user=user.title or user.name)), 'success')
            user.last_login_date = datetime.now()
            return HTTPFound(location=came_from, headers=headers)
        request.session.flash(_(u"Login failed."), 'error')

    if 'reset-password' in request.POST:
        login = request.params['login']
        user = _find_user(login)
        if user is not None and user.active:
            email_set_password(
                user, request,
                template_name='kotti:templates/email-reset-password.pt')
            request.session.flash(_(
                u"You should be receiving an email with a link to reset your "
                u"password. Doing so will activate your account."), 'success')
        else:
            request.session.flash(
                _(u"That username or email is not known by this system."),
                'error')

    return {
        'url': request.application_url + '/@@login',
        'came_from': came_from,
        'login': login,
        'password': password,
        'register': asbool(get_settings()['kotti.register']),
        }


@view_config(name='logout')
def logout(context, request):
    """
    Logout view.  Always redirects the user to where he came from.

    :result: Redirect to came_from
    :rtype: pyramid.httpexceptions.HTTPFound
    """

    headers = forget(request)
    request.session.flash(_(u"You have been logged out."), 'info')
    location = request.params.get('came_from', request.application_url)
    return HTTPFound(location=location, headers=headers)


class SetPasswordSchema(colander.MappingSchema):
    """
    Schema for the set password form
    """

    #: colander.String
    password = colander.SchemaNode(
        colander.String(),
        title=_(u'Password'),
        validator=colander.Length(min=5),
        widget=CheckedPasswordWidget(),
        )
    #: colander.String
    token = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        )
    #: colander.String
    email = colander.SchemaNode(
        colander.String(),
        title=_(u'Email'),
        widget=HiddenWidget(),
        )
    #: colander.String
    continue_to = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        missing=colander.null,
        )


@view_config(name='set-password', renderer='kotti:templates/edit/simpleform.pt')
def set_password(context, request,
                 success_msg=_(u"You have reset your password.")):
    """ Set password view.  Displays the set password form and handles its form
    submission.

    :param success_msg: Message to display on successful submission handling
    :type success_msg: str or TranslationString

    :result: Redirect response or dictionary passed to the template for
             rendering.
    :rtype: pyramid.httpexceptions.HTTPFound or dict
    """

    form = Form(SetPasswordSchema(), buttons=(Button('submit', _(u'Submit')),))
    rendered_form = None

    if 'submit' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e:
            request.session.flash(_(u"There was an error."), 'error')
            rendered_form = e.render()
        else:
            token = appstruct['token']
            email = appstruct['email']
            user = _find_user(email)
            if (user is not None and
                    validate_token(user, token) and
                    token == user.confirm_token and
                    user.active):
                password = appstruct['password']
                user.password = get_principals().hash_password(password)
                user.confirm_token = None
                headers = remember(request, user.name)
                user.last_login_date = datetime.now()

                location = (appstruct['continue_to'] or
                            resource_url(context, request))
                request.session.flash(success_msg, 'success')
                return HTTPFound(location=location, headers=headers)
            else:
                request.session.flash(
                    _(u"Your password reset token may have expired."), 'error')

    if rendered_form is None:
        rendered_form = form.render(request.params)

    api = template_api(
        context, request,
        page_title=_(u"Reset your password - ${title}.",
                     mapping=dict(title=context.title)),
        )

    return {
        'api': api,
        'form': rendered_form,
        }


@view_config(context=HTTPForbidden, accept='text/html',)
def forbidden_redirect(context, request):
    """ Forbidden redirect view.  Redirects to the login form for anonymous
    users or to the forbidden view for authenticated users.

    :result: Redirect to one of the above.
    :rtype: pyramid.httpexceptions.HTTPFound
    """
    if request.authenticated_userid:
        location = request.application_url + '/@@forbidden'
    else:
        location = request.application_url + '/@@login?' + urlencode(
            {'came_from': request.url})
    return HTTPFound(location=location)


@view_config(context=HTTPForbidden)
def forbidden_view(request):
    """
    Forbidden view.  Raises 403 for requests not originating from a web browser
    like device.

    :result: 403
    :rtype: pyramid.httpexceptions.HTTPForbidden
    """

    return request.exception


@view_config(name='forbidden', renderer='kotti:templates/forbidden.pt')
def forbidden_view_html(request):
    """
    Forbidden view for browsers.

    :result: empty dictionary passed to the template for rendering
    :rtype: dict
    """

    return {}


def includeme(config):
    config.scan(__name__)
