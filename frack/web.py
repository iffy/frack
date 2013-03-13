# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
"""
Klein-based web service
"""

from twisted.web.resource import NoResource, Resource
from twisted.internet import defer
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
        self._cache = {}
        loader = FileSystemLoader(template_root)
        self.jenv = Environment(loader=loader)
        self.jenv.globals['static_root'] = '/static'
        self.jenv.filters['wikitext'] = wiki_to_html


    def render(self, request, name, params=None):
        params = params or {}
        params.update({
            'user': getUser(request),
            'urlpath': request.URLPath(),
        })
        dlist = []
        for k,v in list(params.items()):
            # I'm just making them all deferred so that the list is homogeneous.
            # If it's slowing things down too much, then fix it.
            d = defer.maybeDeferred(lambda:v).addCallback(lambda v:(k,v))
            dlist.append(d)
        d = defer.gatherResults(dlist, consumeErrors=True)
        return d.addCallback(self._render, request, name)


    def _render(self, items, request, name):
        params = dict(items)
        template = self.jenv.get_template(name)
        return template.render(params).encode('utf-8')

    @app.route('/newticket', methods=['GET'])
    def create_GET(self, request):        
        return self.render(request, 'ticket_create.html', {
            'components': self.getComponents(request),
            'milestones': self.getMilestones(request),
            'severities': self.getSeverities(request),
            'priorities': self.getPriorities(request),
            'resolutions': self.getResolutions(request),
            'ticket_types': self.getTicketTypes(request),
        })

    @app.route('/newticket', methods=['POST'])
    def create_POST(self, request):
        def one(name):
            return request.args.get(name, [''])[0]
        data = {
            'type': one('field_type'),
            'component': one('field_component'),
            # no severity
            'priority': one('field_priority'),
            # no owner
            'cc': one('field_cc'),
            # no version
            'milestone': one('field_milestone'),
            #'status': one('field_status'),
            # no resolution
            'summary': one('field_summary'),
            'description': one('field_description'),
            'keywords': one('field_keywords'),
        }
        store = TicketStore(self.runner, getUser(request))
        d = store.createTicket(data)

        def created(ticket_number, request):
            request.redirect('ticket/%d' % (ticket_number,))
        # XXX return something nice when not authenticated.
        return d.addCallback(created, request)


    @app.route('/ticket/<int:ticketNumber>')
    def ticket(self, request, ticketNumber):
        user = getUser(request)
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


    def _cacheValue(self, value, name):
        self._cache[name] = value
        return value


    def getCachedValue(self, name, func, *args, **kwargs):
        if name in self._cache:
            return defer.succeed(self._cache[name])
        d = defer.maybeDeferred(func, *args, **kwargs)
        return d.addCallback(self._cacheValue, name)


    def getComponents(self, request):
        store = TicketStore(self.runner, getUser(request))
        return self.getCachedValue('components', store.fetchComponents)


    def getMilestones(self, request):
        store = TicketStore(self.runner, getUser(request))
        return self.getCachedValue('milestones', store.fetchMilestones)


    def getSeverities(self, request):
        store = TicketStore(self.runner, getUser(request))
        return self.getCachedValue('severities',
            store.fetchEnum, 'severity')


    def getPriorities(self, request):
        store = TicketStore(self.runner, getUser(request))
        return self.getCachedValue('priorities',
            store.fetchEnum, 'priority')


    def getResolutions(self, request):
        store = TicketStore(self.runner, getUser(request))
        return self.getCachedValue('resolutions',
            store.fetchEnum, 'resolution')


    def getTicketTypes(self, request):
        store = TicketStore(self.runner, getUser(request))
        return self.getCachedValue('ticket_types',
            store.fetchEnum, 'ticket_type')



