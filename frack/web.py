# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
"""
Klein-based web service
"""

from twisted.web.resource import NoResource, Resource
from jinja2 import Environment, FileSystemLoader
from frack.db import NotFoundError, TicketStore
from klein import Klein


def wiki_to_html(data):
    """
    This should produce HTML formatted like trac formats wiki text.

    XXX for now, I'm just putting WIKI in front to signal in the UI that
    something is happening
    """
    import cgi
    return '<div class="wikied">&lt;wiki&gt;' + cgi.escape(data) + '&lt;/wiki&gt;</div>'



def setUser(request, user):
    """
    Associate this request with a user.  This assumes that you've already done
    authentication and that this request should, in fact, be associated with
    the given user.

    @param request: A web request
    @param user: a string username
    """
    # XXX for now, I'm just putting it right on the request.  It could be
    # improved later.
    request.authenticated_user = user


def getUser(request):
    """
    Get the already-authenticated username for this request.
    """
    # see setUser for why the implementation is thus
    return getattr(request, 'authenticated_user', None)



class FakeAuthenticatorDontActuallyUseExceptForTesting(Resource):
    """
    I provide passwordless authentication for testing.
    """


    def __init__(self, wrapped):
        Resource.__init__(self)
        self.wrapped = wrapped


    def getChild(self, path, request):
        setUser(request, path)
        return self.wrapped



class TicketApp(object):

    app = Klein()


    def __init__(self, runner, template_root):
        self.runner = runner
        loader = FileSystemLoader(template_root)
        self.jenv = Environment(loader=loader)
        self.jenv.globals['static_root'] = '/static'
        self.jenv.filters['wikitext'] = wiki_to_html


    def render(self, request, name, params=None):
        params = params or {}
        params.update({
            'user': getUser(request),
        })
        template = self.jenv.get_template(name)
        return template.render(params).encode('utf-8')


    @app.route('/ticket/<int:ticketNumber>')
    def ticket(self, request, ticketNumber):
        user = getUser(request)
        print 'user', user
        print 'runner', self.runner
        store = TicketStore(self.runner, user)

        d = store.fetchTicket(ticketNumber)
        d.addCallback(self._renderTicket, request)
        d.addErrback(self._notFound, request)
        return d


    def _renderTicket(self, ticket, request):
        return self.render(request, 'ticket.html', {
            'urlpath': request.URLPath(),
            'ticket': ticket,
        })


    def _notFound(self, err, request):
        err.trap(NotFoundError)
        return NoResource().render(request)


    def resource(self):
        return self.app.resource()
