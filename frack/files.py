# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
from twisted.internet import defer
from twisted.python.filepath import FilePath


class DiskFileStore(object):


    def __init__(self, root):
        """
        @param root: root path for storing files.
        """
        self.root = FilePath(root)


    def put(self, kind, id, filename, fh):
        """
        Save a file.

        @param kind: Kind of file (e.g. C{'ticket'} or C{'wiki'})
        @param id: kind id (ticket id or wiki page name)
        @param filename: name of the file
        @param fh: file-like object from which the contents will be read.

        @return: A C{Deferred} which fires with the filesize once the file has
            been saved to disk.
        """
        fpath = self.root.child(kind).child(id).child(filename)
        try:
            fpath.parent().makedirs()
        except OSError:
            pass
        fpath.setContent(fh.read())
        return defer.succeed(fh.tell())