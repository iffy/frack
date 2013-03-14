# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
"""
Klein-based web service
"""

import time
from email import utils

from jinja2 import Environment, FileSystemLoader

from klein import Klein

from twisted.web.resource import NoResource, Resource
from twisted.internet import defer

from frack.db import NotFoundError, TicketStore



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

        # Give me the first error, not a FirstError
        d.addErrback(lambda err: err.value.subFailure)
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
            'owner': one('field_owner'),
            'cc': one('field_cc'),
            # no version
            'milestone': one('field_milestone'),
            #'status': one('field_status'),
            # no resolution
            'summary': one('field_summary'),
            'description': one('field_description'),
            'keywords': one('field_keywords'),
            'branch': one('field_branch'),
            'branch_author': one('field_branch_author'),
            'launchpad_bug': one('field_launchpad_bug'),
        }
        store = TicketStore(self.runner, getUser(request))
        d = store.createTicket(data)

        def created(ticket_number, request):
            request.redirect('ticket/%d' % (ticket_number,))
        # XXX return something nice when not authenticated.
        return d.addCallback(created, request)


    @app.route('/users', methods=['GET', 'HEAD'])
    def users_GET(self, request):
        """
        Get a list of all the users in the system
        """
        # XXX this is all fake
        last_modified = time.mktime((2001, 1, 1, 0, 0, 0, 0, 0, 0))

        if_modified_since = request.getHeader('if-modified-since')
        if if_modified_since:
            parsed = utils.parsedate(if_modified_since)
            if_modified_since = time.mktime(parsed)
            if last_modified < if_modified_since:
                request.setResponseCode(304)
                return 'Not Modified'

        # ask the client to cache this
        request.setHeader('Last-Modified', utils.formatdate(last_modified))
        return self.render(request, 'select.html', {
            # the current drop down on twisteds' site has about 4000 options
            'options': ['jim', 'bob', 'sam', 'joe']*1000
        })


    @app.route('/ticket/<int:ticketNumber>', methods=['GET'])
    def ticket(self, request, ticketNumber):
        user = getUser(request)
        store = TicketStore(self.runner, user)

        return self.render(request, 'ticket.html', {
            'ticket': store.fetchTicket(ticketNumber),
            'components': self.getComponents(request),
            'milestones': self.getMilestones(request),
            'severities': self.getSeverities(request),
            'priorities': self.getPriorities(request),
            'resolutions': self.getResolutions(request),
            'ticket_types': self.getTicketTypes(request),
        }).addErrback(self._notFound, request)


    @app.route('/ticket/<int:ticketNumber>', methods=['POST'])
    def ticket_POST(self, request, ticketNumber):
        user = getUser(request)
        store = TicketStore(self.runner, user)

        def one(name):
            return request.args.get(name, [''])[0]
        # XXX this is WET from the create handler above
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
            #'description': one('field_description'),
            'keywords': one('field_keywords'),
            'branch': one('field_branch'),
            'branch_author': one('field_branch_author'),
            'launchpad_bug': one('field_launchpad_bug'),
        }
        comment = one('comment')
        action = one('action')
        if action == 'leave':
            pass
        elif action == 'reopen':
            # XXX check that it's actually closed
            data['resolution'] = ''
            data['status'] = 'reopen'
        elif action == 'resolve':
            # XXX check that it's not closed
            data['resolution'] = one('action_resolve_resolve_resolution')
            data['status'] = 'closed'
        elif action == 'reassign':
            # XXX should status = 'assigned' ?
            data['owner'] = one('action_reassign_reassign_owner')
        elif action == 'accept':
            data['owner'] = user
            data['status'] = 'assigned'
        else:
            request.setResponseCode(400)
            return 'not a valid action'


        d = store.updateTicket(ticketNumber, data, comment)
        def cb(ignore, request, ticketNumber):
            request.redirect(str(ticketNumber))
            return ''
        d.addCallback(cb, request, ticketNumber)
        return d.addErrback(lambda err: 'There was an error')


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



