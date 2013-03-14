import StringIO, json

from twisted.trial import unittest
from twisted.internet import defer
from twisted.python.failure import Failure
from twisted.web.test.test_web import DummyRequest

from frack.responder import FrackResponder
from frack.wiring import (JSONRPCFace, UNKNOWN_ERROR, PARSE_ERROR,
                          METHOD_NOT_FOUND, INVALID_REQUEST)
from frack.test.test_responder import FAKETICKET


class JSONRPCTests(unittest.TestCase):

    """
    Tests for JSON-RPC integration with AMP commands.
    """

    def mkface(self, response):
        """
        Create a JSONRPCFace with stub data.
        """
        class FakeStore(object):
            def fetchTicket(f, id):
                return defer.succeed(response)
        f = FrackResponder(FakeStore(), '')
        return JSONRPCFace(f)

    def test_locateResponder(self):
        """
        `JSONRPCFace._locateResponder` returns a method for the
        appropriate AMP responder.
        """
        face = self.mkface(FAKETICKET)
        m = face._locateResponder("FetchTicket")
        d = m(id=1, asHTML=False)
        self.assertEqual(d.result, FAKETICKET)


    def test_locate_success(self):
        """
        Successful lookups of responders result in responder invocation.
        """
        qid = 7
        f = self.mkface(FAKETICKET)
        req = DummyRequest([])
        req.content = StringIO.StringIO(json.dumps({"jsonrpc": "2.0",
                                                    "id": qid,
                                                    "method": "FetchTicket",
                                                    "params": {"id": 1,
                                                               "asHTML": False}}))
        f.render(req)
        response = json.loads(''.join(req.written))
        self.assertEquals(response, {"jsonrpc": "2.0",
                                     "result": FAKETICKET,
                                     "id": qid})


    def test_locate_failure(self):
        """
        Requests to nonexistent methods return METHOD_NOT_FOUND.
        """
        qid = 7
        f = self.mkface(FAKETICKET)
        req = DummyRequest([])
        req.content = StringIO.StringIO(json.dumps({"jsonrpc": "2.0",
                                                    "id": qid,
                                                    "method": "ImaginaryMethod",
                                                    "params": {}}))
        f.render(req)
        response = json.loads(''.join(req.written))
        self.assertEquals(response, {"jsonrpc": "2.0",
                                     "error":
                                         {'code': METHOD_NOT_FOUND,
                                          "message":
                                              "Unhandled Command: 'ImaginaryMethod'"},
                                     "id": qid})

    def test_invoke_failure(self):
        """
        Requests for methods that fail return failure responses.
        """
        qid = 7
        err = RuntimeError("Something broke")
        f = self.mkface(Failure(err))
        req = DummyRequest([])
        req.content = StringIO.StringIO(json.dumps({"jsonrpc": "2.0",
                                                    "id": qid,
                                                    "method": "FetchTicket",
                                                    "params": {"id": -1,
                                                               "asHTML": False}}))
        f.render(req)
        self.flushLoggedErrors(RuntimeError)
        response = json.loads(''.join(req.written))
        self.assertEquals(response, {"jsonrpc": "2.0",
                                     "error":
                                         {'code': UNKNOWN_ERROR,
                                          "message": str(err)},
                                     "id": qid})

    def test_parse_failure(self):
        """
        Requests that aren't JSON objects receive failure responses.
        """
        req = DummyRequest([])
        req.content = StringIO.StringIO("<html><head><title>You may already"
                                        " be a winner</title</head></html>")
        f = self.mkface(None)
        f.render(req)
        response = json.loads(''.join(req.written))
        self.assertEquals(response, {"jsonrpc": "2.0",
                                     "error":
                                        {'code': PARSE_ERROR,
                                         "message":
                                             "No JSON object could be decoded"},
                                     "id": None})


    def test_request_failure(self):
        """
        JSON objects that aren't JSON-RPC requests receive failure
        responses.
        """
        req = DummyRequest([])
        req.content = StringIO.StringIO("{}")
        f = self.mkface(None)
        f.render(req)
        response = json.loads(''.join(req.written))
        self.assertEquals(response, {"jsonrpc": "2.0",
                                     "error":
                                        {'code': INVALID_REQUEST,
                                         "message":
                                             "Not a JSON-RPC request"},
                                     "id": None})
