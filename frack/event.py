# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from collections import defaultdict

from twisted.internet import defer
from twisted.python import log



class LossyExchange(object):
    """
    I deliver events to all my subscribers, and ignore any delivery failures.
    """

    def __init__(self):
        self._subscribers = defaultdict(lambda:[])


    def subscribe(self, name, func):
        """
        Subscribe a function to be called for each event emitted.

        @param name: Name of events to watch
        @param func: Function to call when event is emitted.
        """
        self._subscribers[name].append(func)


    def emit(self, name, message):
        """
        Emit a message to all subscribers.

        @return: A C{Deferred} which will always callback (never errback) to
            indicate that the each subscriber acknowledged receipt or failed.
        """
        def eb(err, name, func, message):
            log.msg('Delivery failed name=%r func=%r message=%r' % (
                        name, func, message))
        dlist = []
        for func in self._subscribers[name]:
            d = defer.maybeDeferred(func, message)
            d.addErrback(eb, name, func, message)
            dlist.append(d)
        return defer.gatherResults(dlist)

