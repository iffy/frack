# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.cred import error
from twisted.internet import defer
from zope.interface.verify import verifyObject


from frack.auth import (InMemoryAuthStore, TokenCredentials,
                        ITokenCredentials, TokenChecker, User)



class UserTest(TestCase):


    def test_attrs(self):
        """
        Should have a username
        """
        u = User('foo')
        self.assertEqual(u.name, 'foo')



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



class TokenCredentialsTest(TestCase):


    def test_ITokenCredentials(self):
        verifyObject(ITokenCredentials, TokenCredentials('foo'))



class TokenCheckerTest(TestCase):


    @defer.inlineCallbacks
    def test_works(self):
        """
        You can check the credentials of TokenCredentials
        """
        store = InMemoryAuthStore()
        key = yield store.getToken('user')

        cred = TokenCredentials(key)

        checker = TokenChecker(store)
        avatarId = yield checker.requestAvatarId(cred)
        self.assertEqual(avatarId, 'user')


    def test_unauthorized(self):
        """
        If the token is no good, don't get an avatarId
        """
        store = InMemoryAuthStore()

        cred = TokenCredentials('bogus-key')

        checker = TokenChecker(store)
        self.assertFailure(checker.requestAvatarId(cred),
                           error.UnauthorizedLogin)



