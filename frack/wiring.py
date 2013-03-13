# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Components for connecting responder code to AMP and JSON-RPC network
transports.
"""

import types
try:
    import json
except ImportError:
    import simplejson as json

from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.internet.endpoints import serverFromString
from twisted.internet.defer import maybeDeferred
from twisted.application.service import Service
from twisted.protocols import amp
from twisted.web import static
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET, Site

from frack.web import TicketApp

class AMPFactory(ServerFactory):
    """
    Factory for listening for AMP requests.

    @param responder: An object that provides responders to AMP
    commands.
    """
    def __init__(self, responder):
        self.responder = responder


    def buildProtocol(self, addr):
        disp = amp.BoxDispatcher(self.responder)
        a = amp.AMP(boxReceiver=disp, locator=self.responder)
        a.factory = self
        return a



class AMPService(Service):
    """
    Service for AMP listener.

    @param port: An endpoint description, suitable for
    `serverToString`.

    @param responder: An object providing responders for AMP commands.
    """
    def __init__(self, port, responder):
        self.port = port
        self.responder = responder


    def startService(self):
        self.endpoint = serverFromString(reactor, self.port)
        self.endpoint.listen(AMPFactory(self.responder))



class WebService(Service):
    """
    Service for plain web interface for tickets

    @param port: An endpoint description, suitable for `serverToString`.
    """
    def __init__(self, port, mediaPath, runner, templateRoot):
        self.port = port
        self.root = Resource()
        self.root.putChild('tickets', TicketApp(runner, templateRoot).resource())
        self.root.putChild('static', static.File(mediaPath))
        self.site = Site(self.root)


    def startService(self):
        self.endpoint = serverFromString(reactor, self.port)
        self.endpoint.listen(self.site)



class JSONRPCService(Service):
    """
    Service for JSON-RPC listener and web client.

    @param port: An endpoint description, suitable for
    `serverToString`.

    @param responder: An object providing responders for AMP commands.

    @param mediaPath: A filesystem path containing web client files.
    """
    def __init__(self, port, responder, mediaPath):
        self.port = port
        self.responder = responder
        self.mediaPath = mediaPath
        self.root = Resource()
        self.root.putChild('amp', JSONRPCFace(self.responder))
        self.root.putChild('ui', static.File(self.mediaPath))
        self.site = Site(self.root)

    def startService(self):
        self.endpoint = serverFromString(reactor, self.port)
        self.endpoint.listen(self.site)



(INVALID_REQUEST, PARSE_ERROR,
 UNKNOWN_ERROR, METHOD_NOT_FOUND
) = (-32600, -32700,
      -32603, -32601)

class JSONRPCFace(Resource):
    """
    A wrapper providing JSON-RPC access to AMP commands.

    @param responder: An object providing responders for AMP commands.
    """

    def __init__(self, responder):
        Resource.__init__(self)
        self.responder = responder



    def _serialize(self, response, request):
        request.write(json.dumps(response))
        request.finish()


    def _err(self, failure, request, qid):
        return self._fail(request, UNKNOWN_ERROR,
                          str(failure.value), qid)


    def _fail(self, request, code, msg, qid):
        self._serialize({"jsonrpc": "2.0",
                         "error":
                             {"code": code,
                              "message": msg},
                         "id": qid},
                        request)


    def _succeed(self, result, request, qid):
        self._serialize({"jsonrpc": "2.0",
                         "result": result,
                         "id": qid},
                        request)


    def _locateResponder(self, name):
        cd = self.responder._commandDispatch
        if name in cd:
            commandClass, responderFunc = cd[name]
            responderMethod = types.MethodType(
                responderFunc, self.responder, self.responder.__class__)
            return responderMethod


    def render(self, request):
        try:
            q = json.loads(request.content.read())
        except ValueError:
            self._fail(request, PARSE_ERROR,
                      "No JSON object could be decoded", None)
            return NOT_DONE_YET
        qid = q.get('id')
        if 'method' not in q:
            self._fail(request, INVALID_REQUEST, "Not a JSON-RPC request", qid)
            return NOT_DONE_YET
        resp = self._locateResponder(q['method'])
        if resp is None:
            self._fail(request, METHOD_NOT_FOUND,
            "Unhandled Command: %r" % (q['method'].encode('ascii'),), qid)
        else:
            self._invoke(request, resp, q.get('params') or {}, qid)
        return NOT_DONE_YET


    def _invoke(self, request, responder, params, qid):
        d = maybeDeferred(responder,
                          **dict([(k.encode('ascii'), v)
                                  for (k, v) in params.iteritems()]))
        d.addCallback(self._succeed, request, qid)
        d.addErrback(self._err, request, qid)
        return d


    def getChild(self, path, request):
        if path == '':
            return self
        else:
            return Resource.getChild(self, path, request)
