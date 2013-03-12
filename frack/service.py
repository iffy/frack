# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
import os, pwd, socket
from twisted.python import usage
from twisted.application.service import Service
from twisted.python.util import sibpath
from frack.db import DBStore, sqlite_connect, postgres_probably_connect
from frack.responder import FrackResponder
from frack.wiring import AMPService, JSONRPCService

class FrackService(Service):

    def __init__(self, dbconnection, ampPort, jsonRPCPort, mediaPath,
                 baseUrl, templateRoot, fakeAuth=False):
        self.store = DBStore(dbconnection)
        self.responder = FrackResponder(self.store, baseUrl)
        self.ampPort = ampPort
        self.jsonRPCPort = jsonRPCPort
        self.mediaPath = mediaPath
        self.templateRoot = templateRoot
        self.amp = AMPService(self.ampPort, self.responder)
        self.jsonrpc = JSONRPCService(self.jsonRPCPort, self.responder,
                                      self.mediaPath, self.store,
                                      self.templateRoot, fakeAuth)

    def startService(self):
        self.amp.startService()
        self.jsonrpc.startService()



class Options(usage.Options):
    synopsis = '[frack options]'

    optFlags = [
      ['fakeauthfortesting', None, "Make authentication as simple as putting "
                                   "the desired username in the url"],
    ]

    optParameters = [['postgres_db', None, None,
                      'Name of Postgres database to connect to.'],

                     ['postgres_user', 'u', pwd.getpwuid(os.getuid())[0],
                      'Username for connecting to Postgres.'],

                     ['sqlite_db', None, None,
                      'Path to SQLite database to connect to.'],

                     ['amp', 'a', 'tcp:1352',
                      'Service description for the AMP listener.'],

                     ['jsonrpc', 'j', 'tcp:1353',
                      'Service description for the JSON-RPC listener.'],

                     ['mediapath', 'p',
                      os.path.join(os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))), 'webclient'),
                      'Location of media files for web UI.'],
                     ['baseUrl', 'b', 'http://%s:1353/' % (socket.getfqdn(),),
                      'Domain web client will be accessed from'],

                     ['templates', 't',
                      os.path.join(os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))), 'templates'),
                      'Location of jinja2 template files.'],
    ]

    longdesc = """A postmodern deconstruction of the Python web-based issue tracker."""



def makeService(config):

    if config['postgres_db'] and config['sqlite_db']:
        raise usage.UsageError("Only one of 'sqlite_db' and 'postgres_db' can be specified.")
    if not config['postgres_db'] and not config['sqlite_db']:
        config['postgres_db'] = 'trac'

    if config['postgres_db']:
        connection = postgres_probably_connect(config['postgres_db'], config['postgres_user'])
    elif config['sqlite_db']:
        connection = sqlite_connect(config['sqlite_db'])

    return FrackService(dbconnection=connection,
                        ampPort=config['amp'],
                        jsonRPCPort=config['jsonrpc'],
                        mediaPath=config['mediapath'],
                        baseUrl=config['baseUrl'],
                        templateRoot=config['templates'],
                        fakeAuth=config['fakeauthfortesting'])
