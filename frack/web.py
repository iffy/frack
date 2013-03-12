# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
"""
Klein-based web service
"""

from twisted.web.resource import NoResource
from jinja2 import Environment, FileSystemLoader
from frack.db import NotFoundError
from klein import Klein


def wiki_to_html(data):
    """
    This should produce HTML formatted like trac formats wiki text.

    XXX for now, I'm just putting WIKI in front to signal in the UI that
    something is happening
    """
    import cgi
    return '<div class="wikied">&lt;wiki&gt;' + cgi.escape(data) + '&lt;/wiki&gt;</div>'




class TicketApp(object):

    app = Klein()


    def __init__(self, store, template_root):
        self.store = store
        loader = FileSystemLoader(template_root)
        self.jenv = Environment(loader=loader)
        self.jenv.globals['static_root'] = '/ui'
        self.jenv.filters['wikitext'] = wiki_to_html


    def render(self, name, params=None):
        params = params or {}
        template = self.jenv.get_template(name)
        return template.render(params).encode('utf-8')


    @app.route('/ticket/<int:ticketNumber>')
    def ticket(self, request, ticketNumber):
        d = self.store.fetchTicket(ticketNumber)
        d.addCallback(self.store.groupComments)
        d.addCallback(self._renderTicket, request)
        d.addErrback(self._notFound, request)
        return d


    def _renderTicket(self, ticket, request):
        return self.render('ticket.html', {
            'urlpath': request.URLPath(),
            'ticket': ticket,
        })


    def _notFound(self, err, request):
        err.trap(NotFoundError)
        return NoResource().render(request)


    def resource(self):
        return self.app.resource()
