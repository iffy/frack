# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Components for simple web interface.
"""

from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.application.service import Service
from twisted.web import static
from twisted.web.resource import Resource
from twisted.web.server import Site

from jinja2 import FileSystemLoader, Environment

from frack.db import AuthStore
from frack.web import TicketApp, PersonaAuthApp, Renderer, TracAuthWrapper
from frack.files import DiskFileStore



class WebService(Service):
    """
    Service for plain web interface for tickets

    @param port: An endpoint description, suitable for `serverToString`.
    """
    def __init__(self, port, mediaPath, runner, templateRoot, fileRoot, baseUrl,
                 secureCookies=True, frackRootPath=''):
        self.port = port

        self.root = Resource()
        file_store = DiskFileStore(fileRoot)

        loader = FileSystemLoader(templateRoot)
        jinja_env = Environment(loader=loader)
        jinja_env.globals['frack_root'] = frackRootPath
        renderer = Renderer(jinja_env)

        auth_store = AuthStore(runner)
        
        # ticket app
        ticket_app = TicketApp(runner, renderer, file_store,
                               frackRootPath=frackRootPath)
        self.root.putChild('tickets',
            TracAuthWrapper(auth_store, ticket_app.app.resource()))

        # authentication/registration app
        auth_app = PersonaAuthApp(runner, renderer, audience=baseUrl,
                                  frackRootPath=frackRootPath)
        auth_app.secure_cookie = secureCookies
        self.root.putChild('auth',
            TracAuthWrapper(auth_store, auth_app.app.resource()))

        self.root.putChild('static', static.File(mediaPath))
        self.root.putChild('files', static.File(fileRoot))
        self.site = Site(self.root)


    def startService(self):
        self.endpoint = serverFromString(reactor, self.port)
        self.endpoint.listen(self.site)
