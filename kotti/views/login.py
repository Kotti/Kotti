import colander
from deform import Form
from deform import ValidationFailure
from deform.widget import CheckedPasswordWidget
from deform.widget import HiddenWidget
from formencode.validators import Email
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.security import forget
from pyramid.url import resource_url

from kotti.message import validate_token
from kotti.message import send_set_password
from kotti.resources import get_root
from kotti.resources import Node
from kotti.security import get_principals
from kotti.views.util import TemplateAPIEdit

def _find_user(login):
    principals = get_principals()
    principal = principals.get(login)
    if principal is None:
        try:
            Email().to_python(login)
        except Exception:
            pass
        else:
            results = [r for r in principals.search(email=login)]
            if results:
                principal = results[0]
    return principal

def login(context, request):
    root = get_root(request)
    api = TemplateAPIEdit(root, request)
    principals = get_principals()

    came_from = request.params.get('came_from', request.url)
    login, password = u'', u''

    if 'submit' in request.POST:
        login = request.params['login']
        password = request.params['password']
        user = _find_user(login)

        if (user is not None and user.active and 
            user.password == principals.hash_password(password)):
            headers = remember(request, login)
            request.session.flash(
                u"Welcome, %s!" % user.title or user.name, 'success')
            return HTTPFound(location=came_from, headers=headers)
        request.session.flash(u"Login failed.", 'error')

    if 'reset-password' in request.POST:
        login = request.params['login']
        user = _find_user(login)
        if user is not None:
            send_set_password(user, request, templates='reset-password')
            request.session.flash(
                u"You should receive an email with a link to reset your "
                u"password momentarily.", 'success')
        else:
            request.session.flash(
                "That username or email is not known to us.", 'error')

    return {
        'api': api,
        'url': request.application_url + '/@@login',
        'came_from': came_from,
        'login': login,
        'password': password,
        }

def logout(context, request):
    headers = forget(request)
    request.session.flash(u"You have been logged out.")
    location = request.params.get('came_from', request.application_url)
    return HTTPFound(location=location, headers=headers)

class SetPasswordSchema(colander.MappingSchema):
    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5),
        widget=CheckedPasswordWidget(),
        )
    token = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        )
    email = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        )

def set_password(context, request,
                 success_msg=u"You've reset your password successfully."):
    form = Form(SetPasswordSchema(), buttons=('submit',))
    rendered_form = None

    if 'submit' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e:
            request.session.flash(u"There was an error.", 'error')
            rendered_form = e.render()
        else:
            token = appstruct['token']
            email = appstruct['email']
            principals = get_principals()
            results = principals.search(email=email)
            if results:
                user = results[0]
                if validate_token(user, token) and token == user.confirm_token:
                    password = appstruct['password']
                    user.password = principals.hash_password(password)
                    user.confirm_token = None
                    headers = remember(request, user.name)
                    location = resource_url(context, request)
                    request.session.flash(success_msg, 'success')
                    return HTTPFound(location=location, headers=headers)
            request.session.flash(
                u"Your password reset token may have expired.", 'error')

    if rendered_form is None:
        rendered_form = form.render(request.params.items())

    api = TemplateAPIEdit(
        context, request,
        page_title=u"Reset your password - %s" % context.title,
        )

    return {
        'api': api,
        'form': rendered_form,
        }

def includeme(config):
    config.add_view(
        login,
        context='pyramid.exceptions.Forbidden',
        renderer='../templates/edit/login.pt',
        )

    config.add_view(
        login,
        name='login',
        context=Node,
        renderer='../templates/edit/login.pt',
        )

    config.add_view(
        logout,
        name='logout',
        )

    config.add_view(
        set_password,
        name='set-password',
        renderer='../templates/edit/simpleform.pt',
        )
