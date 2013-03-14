# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.internet import defer


from frack.event import LossyExchange



class LossyExchangeTest(TestCase):


    def test_subscribe(self):
        """
        You can subscribe to named events.
        """
        x = LossyExchange()
        called = []
        x.subscribe('foo', called.append)
        x.emit('foo', 'something')
        self.assertEqual(called, ['something'])


    def test_subscribe_many(self):
        """
        Everyone on the list should get the message, even if a function raises
        an exception during processing.
        """
        x = LossyExchange()
        called_a = []
        def a(x):
            called_a.append(x)
            raise Exception()
        called_b = []

        x.subscribe('foo', a)
        x.subscribe('foo', called_b.append)

        x.emit('foo', 'something')
        self.assertEqual(called_a, ['something'])
        self.assertEqual(called_b, ['something'])


    def test_deferred(self):
        """
        I shouldn't return until all the handlers have returned.
        """
        x = LossyExchange()

        d = defer.Deferred()

        x.subscribe('foo', lambda x:defer.succeed(True))
        x.subscribe('foo', lambda x:defer.fail(Exception()))
        x.subscribe('foo', lambda x:d)

        r = x.emit('foo', 'message')
        self.assertFalse(r.called)

        d.callback('something')
        self.assertTrue(r.called)


    def test_diable(self):
        """
        You can disable and enable events by name
        """
        x = LossyExchange()
        a = []
        b = []
        x.subscribe('foo', a.append)
        x.subscribe('bar', b.append)

        x.disable('foo')
        x.emit('foo', 'something')
        self.assertEqual(a, [], "Should not emit because it's disabled")
        x.emit('bar', 'something')
        self.assertEqual(b, ['something'], "Only the named event should be "
                         "disabled")

        x.enable('foo')
        x.emit('foo', 'something')
        self.assertEqual(a, ['something'], "Should be enabled now")
