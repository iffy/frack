# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
from twisted.internet import defer
from StringIO import StringIO


from frack.files import DiskFileStore


class DiskFileStoreTest(TestCase):


    @defer.inlineCallbacks
    def test_put(self):
        """
        You can save files
        """
        root = FilePath(self.mktemp())
        root.makedirs()
        store = DiskFileStore(root.path)

        fh = StringIO('some data')
        size = yield store.put('ticket', '1234', 'foo.txt', fh)

        self.assertEqual(root.child('ticket').child('1234').child('foo.txt').getContent(),
                         'some data')
        self.assertEqual(size, len('some data'))
