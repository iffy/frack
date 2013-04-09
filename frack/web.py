# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
"""
Klein-based web service
"""

import time
import cgi
import json
import requests
from email import utils
from datetime import datetime
from urllib import quote_plus

from klein import Klein

from twisted.web.resource import NoResource, Resource
from twisted.web.util import DeferredResource
from twisted.internet import defer, threads

from frack.db import NotFoundError, TicketStore, AuthStore, UnauthorizedError


#------------------------------------------------------------------------------
# authentication

class TracAuthWrapper(Resource):


    def __init__(self, store, child):
        """
        @param store: An AuthStore instance.
        @param child: The resource being wrapped.
        """
        Resource.__init__(self)
        self.store = store
        self.child = child


    def render(self, request):
        d = self._associateUser(request)
        return DeferredResource(d).render(request)


    def getChildWithDefault(self, path, request):
        request.postpath.insert(0, request.prepath.pop())
        d = self._associateUser(request)
        return DeferredResource(d)


    @defer.inlineCallbacks
    def _associateUser(self, request):
        cookie_value = request.getCookie('trac_auth')
        try:
            username = yield self.store.usernameFromCookie(cookie_value)
            setUser(request, username)
        except NotFoundError:
            setUser(request, None)
        defer.returnValue(self.child)



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


def setEmail(email, request):
    """
    Associate an already-authenticated email address with this
    request's session.
    """
    session = request.getSession()
    # XXX very bad, do sessions the right way, eh?
    session.persona_email = email
    return email


def getEmail(request):
    """
    Get the already-authenticated email address associated with this
    request.
    """
    session = request.getSession()
    return getattr(session, 'persona_email', None)


#------------------------------------------------------------------------------
# rendering


class Renderer(object):


    def __init__(self, jinja_env):
        self.jinja_env = jinja_env
        self.jinja_env.globals['static_root'] = '/static'
        self.jinja_env.globals['attachment_root'] = '/files'
        self.jinja_env.globals['raw_attachment_root'] = '/files'

        self.jinja_env.filters['wikitext'] = wiki_to_html
        self.jinja_env.filters['format_reply'] = format_reply
        self.jinja_env.filters['ago'] = relativeTime
        self.jinja_env.filters['isotime'] = isolikeTime
        self.jinja_env.filters['urlencode'] = quote_plus


    def render(self, request, name, params=None):
        params = params or {}
        params.update({
            'user': getUser(request),
            'urlpath': request.URLPath(),
            'logged_in_email': getEmail(request),
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
        template = self.jinja_env.get_template(name)
        return template.render(params).encode('utf-8')


#------------------------------------------------------------------------------
# Jinja filters

def wiki_to_html(data):
    """
    This should produce HTML formatted like trac formats wiki text.

    XXX for now, I'm just putting WIKI in front to signal in the UI that
    something is happening
    """
    return '<div class="wikied">&lt;wiki&gt;' + cgi.escape(data) + '&lt;/wiki&gt;</div>'


def format_reply(text):
    """
    I prefix each line with '> '
    """
    return '\n'.join(['> '+line for line in text.split('\n')])


def pl(i, singular, plural):
    """
    I'm sure this problem has been solved before... and probably with actual
    i18n support :(
    """
    if i == 1:
        return singular
    return plural

def relativeTime(seconds):
    """
    @param seconds: Seconds since epoch

    @return: A string description of the relative distance from C{seconds} to
        now.
    """
    diff = int(time.time()) - int(seconds)
    if diff <= 0:
        # actually in the future.  Should it say that instead?
        return 'just now'

    minutes = diff / 60
    if not minutes:
        return '%d %s ago' % (diff, pl(diff, 'second', 'seconds'))
    hours = minutes / 60
    if not hours:
        return '%d %s ago' % (minutes, pl(minutes, 'minute', 'minutes'))
    days = hours / 24
    if not days:
        return '%d %s ago' % (hours, pl(hours, 'hour', 'hours'))
    weeks = days / 7
    if not weeks:
        return '%d %s ago' % (days, pl(days, 'day', 'days'))
    months = days / 30
    if not months:
        return '%d %s ago' % (weeks, pl(weeks, 'week', 'weeks'))
    years = days / 365
    if not years:
        return '%d %s ago' % (months, pl(months, 'month', 'months'))
    decades = years / 10
    if not decades:
        return '%d %s ago' % (years, pl(years, 'year', 'years'))
    return '%d %s ago' % (decades, pl(decades, 'decade', 'decades'))


def isolikeTime(seconds):
    """
    @param seconds: Seconds since epoch
    @return: A string date like this: C{"2013-03-13T20:41:49-0400"}.
        XXX I'm not sure how to decide what timezone to use.
    """
    dt = datetime.fromtimestamp(seconds)
    return dt.strftime('%Y-%m-%dT%H:%M:%S-0000')






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


    def __init__(self, runner, renderer, file_store, frackRootPath):
        self.runner = runner
        self.file_store = file_store
        self._cache = {}
        self._userList = None
        self._userList_lastModified = None
        self.renderer = renderer
        self.frackRootPath = frackRootPath


    @defer.inlineCallbacks
    def getUserList(self, request):
        """
        Get the list of users and the last time the list was modified returned
        as a deferred tuple.
        """
        if self._userList is None or self._userList_lastModified:
            # need to refresh it
            store = TicketStore(self.runner, getUser(request))
            new_list = yield store.userList()
            self._userList = list(new_list)
            self._userList_lastModified = time.time()

        defer.returnValue((self._userList, self._userList_lastModified))


    def render(self, *args, **kwargs):
        return self.renderer.render(*args, **kwargs)


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
        return self.getUserList(request).addCallback(self.gotUserList, request)


    def gotUserList(self, data, request):
        users, last_modified = data

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
            'options': users,
        })


    @app.route('/ticket/<int:ticket_number>', methods=['GET'])
    def ticket_GET(self, request, ticket_number):
        user = getUser(request)
        store = TicketStore(self.runner, user)

        replyto = request.args.get('replyto', [''])[0]
        if replyto:
            replyto = int(replyto)

        def mergeCommentsAndAttachments(ticket):
            ticket['commentsAndAttachments'] = sorted(ticket['comments'] + ticket['attachments'], key=lambda x:x['time'])
            return ticket

        return self.render(request, 'ticket.html', {
            'ticket': store.fetchTicket(ticket_number).addCallback(mergeCommentsAndAttachments),
            'replyto': replyto,
            'components': self.getComponents(request),
            'milestones': self.getMilestones(request),
            'severities': self.getSeverities(request),
            'priorities': self.getPriorities(request),
            'resolutions': self.getResolutions(request),
            'ticket_types': self.getTicketTypes(request),
        }).addErrback(self._notFound, request)


    @app.route('/ticket/<int:ticket_number>', methods=['POST'])
    def ticket_POST(self, request, ticket_number):
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
        replyto = one('replyto')
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


        d = store.updateTicket(ticket_number, data, comment, replyto)
        def cb(ignore, request, ticket_number):
            request.redirect(str(ticket_number))
            return ''
        d.addCallback(cb, request, ticket_number)
        return d.addErrback(lambda err: 'There was an error')


    @app.route('/ticket/<int:ticket_number>/attachments', methods=['GET'])
    def ticket_attachment_GET(self, request, ticket_number):
        user = getUser(request)
        if not user:
            request.setResponseCode(403)
            return 'you must authenticate to upload attachments'

        return self.render(request, 'ticket_attachment_create.html', {
            'ticket_number': ticket_number,
        })


    @app.route('/ticket/<int:ticket_number>/attachments', methods=['POST'])
    def ticket_attachment_POST(self, request, ticket_number):
        user = getUser(request)        
        if not user:
            # XXX make this nicer
            request.setResponseCode(403)
            return 'you must authenticate'

        # XXX we should probably make sure the ticket exists

        store = TicketStore(self.runner, user)

        description = request.args.get('description', [''])[0]
        ip = request.getClientIP()

        # store metadata in the ticket store (database)
        def storeMeta(size, store, ticket_number, filename, description, ip):
            data = {
                'filename': filename,
                'size': size,
                'description': description,
                'ip': ip,
            }
            return store.addAttachmentMetadata(ticket_number, data)

        # read file from request and save to file store (disk)
        headers = request.getAllHeaders()
        chunk = cgi.FieldStorage(fp=request.content,
                                 headers=headers,
                                 environ={
                                    'REQUEST_METHOD':'POST',
                                    'CONTENT_TYPE': headers['content-type'],
                                })
        keys = list(chunk)
        files = [chunk[key] for key in keys if chunk[key].filename]
        dlist = []
        for f in files:
            d = self.file_store.put('ticket', str(ticket_number),
                                    f.filename, f.file)
            d.addCallback(storeMeta, store, ticket_number, f.filename,
                          description, ip)
            dlist.append(d)
        
        def cb(response, request, ticket_number):
            # XXX this needs better url creation code
            request.redirect('../%d' % (ticket_number,))
            return ''


        def eb(err, request):
            request.setResponseCode(400)
            return ('Error.  Maybe there is already a file by that name on this'
                    ' ticket?')

        d = defer.gatherResults(dlist, consumeErrors=True)
        return d.addCallback(cb, request, ticket_number).addErrback(eb, request)


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



class PersonaAuthApp(object):


    app = Klein()
    verification_url = 'https://verifier.login.persona.org/verify'
    cookie_name = 'trac_auth'
    secure_cookie = True


    def __init__(self, runner, renderer, audience, frackRootPath):
        self.store = AuthStore(runner)
        self.audience = audience
        self.renderer = renderer
        self.frackRootPath = frackRootPath


    def render(self, *args, **kwargs):
        return self.renderer.render(*args, **kwargs)


    @app.route('/login')
    def login(self, request):
        # XXX since I am lame, and want to see this working right now, I'm
        # going to use requests.  I acknowledge the lameness.
        assertion = request.args['assertion'][0]
        d = threads.deferToThread(self._getVerifiedEmail, assertion)
        d.addCallback(setEmail, request)
        
        d.addCallbacks(self.store.usernameFromEmail)
        d.addCallbacks(self._logThemIn, self._emailNotInUse,
                       callbackArgs=(request,), errbackArgs=(request,))
        return d


    def _getVerifiedEmail(self, assertion):
        """
        Verify an assertion with the the provider.
        """
        data = {
            'assertion': assertion,
            'audience': self.audience,
        }
        response = requests.post(self.verification_url, data=data, verify=True)

        if not response.ok:
            raise UnauthorizedError('Verification failed')

        verification_data = json.loads(response.content)

        if verification_data['status'] == 'okay':
            return verification_data['email']
        raise UnauthorizedError('Verification failed')


    def _emailNotInUse(self, err, request):
        """
        This person has authenticated using an email address that isn't
        being used yet.
        """
        err.trap(NotFoundError)
        return self.jsonUserState(err, request)


    def _logThemIn(self, username, request):
        setUser(request, username)
        d = self.store.cookieFromUsername(username)
        d.addCallback(self.setTracCookie, request)
        return d.addCallback(self.jsonUserState, request)


    def setTracCookie(self, cookie_value, request):
        # XXX what kind of expiration should it have?
        # XXX add httponly
        request.addCookie(self.cookie_name, cookie_value.encode('utf-8'),
                          path='/',
                          secure=self.secure_cookie)


    def jsonUserState(self, ignore, request):
        request.setHeader('content-type', 'application/json')
        return json.dumps({
            'email': getEmail(request),
            'user': getUser(request),
        }).encode('utf-8')


    @app.route('/register', methods=['GET'])
    def register_GET(self, request):
        return self.render(request, 'register.html')


    @app.route('/register', methods=['POST'])
    def register_POST(self, request):
        username = request.args['username'][0]
        email = getEmail(request)
        if not email:
            request.setResponseCode(401)
            return 'You need to sign in with your email address'
        
        d = self.store.createUser(email, username)
        return d.addCallback(self.registered, request)


    def registered(self, username, request):
        setUser(request, username)
        d = self.store.cookieFromUsername(username)
        d.addCallback(self.setTracCookie, request)
        d.addCallback(lambda _:self.render(request, 'register.html'))
        return d


    @app.route('/logout')
    def logout(self, request):
        setEmail(None, request)
        setUser(request, None)
        request.addCookie(self.cookie_name, '', path='/', secure=self.secure_cookie)
        return 'logged out'







