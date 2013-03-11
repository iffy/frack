# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Definitions of AMP commands for Frack and responders for them.
"""

import types
from urllib import quote_plus as qp
try:
    import json
except ImportError:
    import simplejson as json
import cgi
from twisted.protocols import amp
from twisted.web import client
from twisted.web.server import NOT_DONE_YET
from twisted.web.resource import Resource
from twisted.internet.defer import maybeDeferred
from twisted.python import log
try:
    import trac
    from trac.wiki.formatter import format_to_html
    from trac.wiki.parser import WikiParser
    from trac.wiki.api import WikiSystem
    from trac.wiki.interwiki import InterWikiMap
except ImportError:
    trac = None

class FetchTicket(amp.Command):
    """
    Requests ticket info from data store.

    @param id: The ticket ID to look up

    @param asHTML: Whether to render comments/description as HTML or
    not. Will use Trac wiki formatting if available.

    Returns all ticket fields, including a list of comments/changes.
    """
    arguments = [('id', amp.Integer()),
                 ('asHTML', amp.Boolean(optional=True))]
    response = [('id', amp.Integer()),
                ('type', amp.Unicode()),
                ('time', amp.Integer()),
                ('changetime', amp.Integer()),
                ('component', amp.Unicode()),
                ('priority', amp.Unicode()),
                ('owner', amp.Unicode()),
                ('reporter', amp.Unicode()),
                ('cc', amp.Unicode()),
                ('status', amp.Unicode()),
                ('resolution', amp.Unicode()),
                ('summary', amp.Unicode()),
                ('description', amp.Unicode()),
                ('raw_description', amp.Unicode()),
                ('keywords', amp.Unicode()),
                ('branch', amp.Unicode()),
                ('branch_author', amp.Unicode()),
                ('launchpad_bug', amp.Unicode()),
                ('attachments', amp.AmpList(['name', amp.Unicode()])),
                ('changes', amp.AmpList([('time', amp.Integer()),
                                         ('author', amp.Unicode()),
                                         ('field', amp.Unicode()),
                                         ('oldvalue', amp.Unicode()),
                                         ('newvalue', amp.Unicode())]))]


class BrowserIDLogin(amp.Command):
    """
    Verifies a BrowserID assertion and looks up a user account. If not
    found, a new one for the given email address is created.

    @param assertion: Assertion blob from BrowserID service.

    Returns the user's email and username, and a key to be used in
    further commands.
    """
    arguments = [('assertion', amp.Unicode())]
    response = [('email', amp.Unicode()),
                ('username', amp.Unicode()),
                ('key', amp.Unicode())]



class UpdateTicket(amp.Command):
    """
    Updates a ticket in the data store with new values for fields.
    """
    arguments = [('id', amp.Integer()),
                 ('key', amp.Unicode()),
                 ('type', amp.Unicode(optional=True)),
                 ('component', amp.Unicode(optional=True)),
                 ('priority', amp.Unicode(optional=True)),
                 ('owner', amp.Unicode(optional=True)),
                 ('reporter', amp.Unicode(optional=True)),
                 ('cc', amp.Unicode(optional=True)),
                 ('status', amp.Unicode(optional=True)),
                 ('resolution', amp.Unicode(optional=True)),
                 ('summary', amp.Unicode(optional=True)),
                 ('description', amp.Unicode(optional=True)),
                 ('keywords', amp.Unicode(optional=True)),
                 ('branch', amp.Unicode(optional=True)),
                 ('branch_author', amp.Unicode(optional=True)),
                 ('launchpad_bug', amp.Unicode(optional=True)),
                 ('comment', amp.Unicode(optional=True))]



class FrackResponder(amp.CommandLocator):
    """
    Home to responders for Frack's AMP/JSON-RPC commands.

    @param store: A data store object, probably a wrapper for a Trac DB.

    @param baseUrl: The URL the web client is available at. (Used by
    BrowserID's "audience" parameter to indicate the site login is
    being done for.)
    """
    def __init__(self, store, baseUrl):
        self.store = store
        self.baseUrl = baseUrl


    def _rewriteTicket(self, ticket, transform):
        ticket['raw_description'] = ticket['description']
        ticket['description'] = transform(ticket['description'])
        for change in ticket['changes']:
            if change['field'] == 'comment':
                change['newvalue'] = transform(change['newvalue'])


    @FetchTicket.responder
    def fetchTicket(self, id, asHTML):
        """
        @see: L{FetchTicket}
        """
        d = self.store.fetchTicket(id)
        def _cleanup(ticket):
            if asHTML:
                if trac:
                    self._rewriteTicket(ticket, safeTracWikiFormat)
                else:
                    self._rewriteTicket(ticket, plaintextFormat)
            return ticket
        d.addCallback(_cleanup)

        def _handleErr(e):
            log.err(e)
            return e
        d.addErrback(_handleErr)
        return d


    @BrowserIDLogin.responder
    def browserIDLogin(self, assertion):
        """
        @see: L{BrowserIDLogin}
        """
        # TODO: Verify SSL cert for this host.
        d = client.getPage("https://verifier.login.persona.org/verify?audience=%s&assertion=%s"
                           % ( self.baseUrl, qp(assertion)), method="POST")
        def _collect(resultData):
            result = json.loads(resultData)
            if result['status'] != 'okay':
                return {'ok': False, 'email': ''}
            return (self.store.lookupByEmail(result['email'])
                    .addCallback(_gotUser, {'ok': True, 'email': result['email']}))
        def _gotUser((key, username), result):
            result['username'] = username
            result['key'] = key
            return result
        return d.addCallback(_collect)


    @UpdateTicket.responder
    def updateTicket(self, key, id, **kwargs):
        self.store.updateTicket(key, id, kwargs)
        return {}


def plaintextFormat(txt):
    return '<pre style="white-space: pre-line">' + cgi.escape(txt) + '</pre>'


def safeTracWikiFormat(txt):
    try:
        return tracWikiFormat(txt)
    except Exception, e:
        log.err(e)
        return plaintextFormat(txt)

def tracWikiFormat(txt):
    WikiSystem.safe_schemes = 'cvs,file,ftp,git,irc,http,https,news,sftp,smb,ssh,svn,svn+ssh'.split(',')
    #WikiSystem.syntax_providers = []
    class Env(object):
        components = {}
        def component_activated(self, _): pass
        def get_db_cnx(self): pass
        def __getitem__(self, key): pass
        project_url = "http://example.com/"
        config = {'intertrac': {}}
    class Context(object):
        def set_hints(self, disable_warnings):
            pass
        resource = None
        req = None
        href = None
        perm = None
        def __call__(self): return self

    env = Env()
    WikiParser.env = env
    InterWikiMap.env = env
    return format_to_html(env, Context, txt, False)
