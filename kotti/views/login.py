from datetime import datetime

import colander
from deform import Button
from deform import Form
from deform import ValidationFailure
from deform.widget import CheckedPasswordWidget
from deform.widget import HiddenWidget
from formencode.validators import Email
from pyramid.encode import urlencode
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.security import authenticated_userid
from pyramid.security import remember
from pyramid.security import forget
from pyramid.url import resource_url

from kotti.message import validate_token
from kotti.message import send_set_password
from kotti.security import get_principals
from kotti.util import _
from kotti.views.util import template_api

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

def login(context, request):
    principals = get_principals()

    came_from = request.params.get(
        'came_from', request.resource_url(context))
    login, password = u'', u''

    if 'submit' in request.POST:
        login = request.params['login']
        password = request.params['password']
        user = _find_user(login)

        if (user is not None and user.active and 
            principals.validate_password(password, user.password)):
            headers = remember(request, login)
            request.session.flash(
                _(u"Welcome, ${user}!",
                  mapping=dict(user=user.title or user.name)), 'success')
            user.last_login_date = datetime.now()
            return HTTPFound(location=came_from, headers=headers)
        request.session.flash(_(u"Login failed."), 'error')

    if 'reset-password' in request.POST:
        login = request.params['login']
        user = _find_user(login)
        if user is not None:
            send_set_password(user, request, templates='reset-password')
            request.session.flash(_(
                u"You should receive an email with a link to reset your "
                u"password momentarily."), 'success')
        else:
            request.session.flash(
                _(u"That username or email is not known to us."), 'error')

    return {
        'url': request.application_url + '/@@login',
        'came_from': came_from,
        'login': login,
        'password': password,
        }

def logout(context, request):
    headers = forget(request)
    request.session.flash(_(u"You have been logged out."))
    location = request.params.get('came_from', request.application_url)
    return HTTPFound(location=location, headers=headers)

class SetPasswordSchema(colander.MappingSchema):
    password = colander.SchemaNode(
        colander.String(),
        title=_(u'Password'),
        validator=colander.Length(min=5),
        widget=CheckedPasswordWidget(),
        )
    token = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        )
    email = colander.SchemaNode(
        colander.String(),
        title=_(u'Email'),
        widget=HiddenWidget(),
        )
    continue_to = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        missing=colander.null,
        )

def set_password(context, request,
                 success_msg=_(u"You've reset your password successfully.")):
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
                token == user.confirm_token):
                password = appstruct['password']
                user.password = get_principals().hash_password(password)
                user.confirm_token = None
                headers = remember(request, user.name)
                location = (appstruct['continue_to'] or
                            resource_url(context, request))
                request.session.flash(success_msg, 'success')
                return HTTPFound(location=location, headers=headers)
            else:
                request.session.flash(
                    _(u"Your password reset token may have expired."), 'error')

    if rendered_form is None:
        rendered_form = form.render(request.params.items())

    api = template_api(
        context, request,
        page_title=_(u"Reset your password - ${title}",
                     mapping=dict(title=context.title)),
        )

    return {
        'api': api,
        'form': rendered_form,
        }

def forbidden_redirect(context, request):
    if authenticated_userid(request):
        location = request.application_url + '/@@forbidden'
    else:
        location = request.application_url + '/@@login?' + urlencode(
            {'came_from': request.url})
    return HTTPFound(location=location)

def forbidden_view(request):
    return request.exception

def includeme(config):
    config.add_view(
        forbidden_redirect,
        context=HTTPForbidden,
        accept='text/html',
        )

    config.add_view(
        forbidden_view,
        context=HTTPForbidden,
        )

    config.add_view(
        name='forbidden',
        renderer='kotti:templates/forbidden.pt',
        )

    config.add_view(
        login,
        name='login',
        renderer='kotti:templates/login.pt',
        )

    config.add_view(
        logout,
        name='logout',
        )

    config.add_view(
        set_password,
        name='set-password',
        renderer='kotti:templates/edit/simpleform.pt',
        )
