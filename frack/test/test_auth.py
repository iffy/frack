# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.internet import defer
from mock import MagicMock


from frack.auth import InMemoryAuthStore, Unauthorized



class InMemoryAuthStoreTest(TestCase):


    def getStore(self):
        return InMemoryAuthStore()


    @defer.inlineCallbacks
    def test_cookie(self):
        """
        You should be able to authenticate a user with cookie tokens
        """
        store = yield self.getStore()
        key = yield store.getToken('user')
        user = yield store.getUserByToken(key)
        self.assertEqual(user, 'user')


    @defer.inlineCallbacks
    def test_getToken_same(self):
        """
        You should get the same token each time you request it for a particular
        user.
        """
        store = yield self.getStore()
        k1 = yield store.getToken('user1')
        k2 = yield store.getToken('user1')
        self.assertEqual(k1, k2, "Should be the same for the same user")
        k3 = yield store.getToken('different user')
        self.assertNotEqual(k1, k3,
                            "Different users should have different tokens")

