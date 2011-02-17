from formencode.validators import Email
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.security import forget

from kotti.security import get_principals
from kotti.resources import get_root
from kotti.resources import Node

def login(context, request):
    from kotti.views.util import TemplateAPIEdit
    root = get_root(request)
    api = TemplateAPIEdit(root, request)
    came_from = request.params.get('came_from', request.url)
    login, password = u'', u''
    if 'submitted' in request.POST:
        login = request.params['login']
        password = request.params['password']
        principals = get_principals()
        principal = principals.get(login)

        if principal is None:
            # Maybe an e-mail address, XXX there should be a nicer way
            # of searching 'principals', maybe add kwargs search back.
            try:
                Email().to_python(login)
            except Exception:
                pass
            else:
                for p in principals.search(login):
                    if p.email == login:
                        principal = p
                        break

        if (principal is not None and
            principal.password == principals.hash_password(password)):
            headers = remember(request, login)
            request.session.flash(
                u"Welcome, %s!" % principal.title or principal.id, 'success')
            return HTTPFound(location=came_from, headers=headers)

        request.session.flash(u"Login failed.", 'error')

    return {
        'api': api,
        'url': request.application_url + '/login',
        'came_from': came_from,
        'login': login,
        'password': password,
        }

def logout(context, request):
    headers = forget(request)
    request.session.flash(u"You have been logged out.")
    location = request.params.get('came_from', request.application_url)
    return HTTPFound(location=location, headers=headers)

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
