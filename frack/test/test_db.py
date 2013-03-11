import sqlite3
from twisted.trial.unittest import TestCase
from twisted.python.util import sibpath
from frack.db import DBStore, UnauthorizedError



class DBTests(TestCase):
    """
    Tests for storage/retrieval.
    """

    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(open(sibpath(__file__, "trac_test.sql")).read())

    def test_fetchTicket(self):
        """
        `fetchTicket` collects data about a single ticket, including
        comments/changes, attachments, and custom fields.
        """

        store = DBStore((sqlite3, self.db))
        d = store.fetchTicket(4712)
        def _check(result):
            self.assertEqual(set(result.keys()),
                             set(["type", "status", "summary", "time", "reporter",
                              "owner", "priority",  "resolution", "component",
                              "keywords", "cc", "branch", "branch_author",
                              "launchpad_bug", "description", "changes",
                              "attachments", "id", "changetime"]))

            self.assertEqual(len(result['changes']), 45)
            self.assertEqual(set(result['changes'][0].keys()),
                             set(["newvalue", "author", "oldvalue", "time", "field"]))

        return d.addCallback(_check)


    def test_lookupByEmail(self):
        """
        `lookupByEmail` looks up a session key and username by the
        email associated with it.
        """
        store = DBStore((sqlite3, self.db))
        d = store.lookupByEmail('alice@example.com')
        def _check(result):
            self.assertEqual(result, ('a331422278bd676f3809e7a9d8600647',
                                      'alice'))
        return d.addCallback(_check)

    def test_createAccountFromEmail(self):
        """
        `lookupByEmail` looks up a session key and username by the
        email associated with it.
        """
        store = DBStore((sqlite3, self.db))
        email = 'bob@example.org'
        d = store.lookupByEmail(email);
        def _check(result):
            key, name = result
            self.assertEqual(name, email)
            c = self.db.execute("select sid, authenticated, value "
                            "from session_attribute "
                            "where name = 'email' ""and value = ?",
                            (email,))
            self.assertEqual(c.fetchall(), [(email, 1, email)])
            c = self.db.execute("select authenticated from session "
                            "where sid = ?", (email,))
            self.assertEqual(c.fetchall(), [(1,)])
            c = self.db.execute("select cookie from auth_cookie where name = ?",
                            (email,))
            self.assertEqual(c.fetchall(), [(key,)])
        return d.addCallback(_check)



    def test_unauthorizedUpdate(self):
        """
        `updateTicket` raises an exception if the key given is
        unacceptable.
        """
        store = DBStore((sqlite3, self.db))
        d = store.updateTicket('not-a-key', 123, {})
        return self.assertFailure(d, UnauthorizedError)


    def test_updateTicket(self):
        """
        `updateTicket` updates the db entry for the given ticket.
        """
        updateData = {
            'type': None,
            'component': None,
            'priority': None,
            'owner': "jethro",
            'reporter': None,
            'cc': None,
            'status': None,
            'resolution': None,
            'summary': "awesome ticket",
            'description': None,
            'keywords': "review",
            #branch is the same as its current value so no change should be recorded
            'branch': "branches/provide-statinfo-accessors-4712",
            'branch_author': "bob",
            'launchpad_bug': None,
            'comment': None
            }
        c = self.db.cursor()
        store = DBStore((sqlite3, self.db))
        c.execute(
            "SELECT summary, owner, keywords from ticket where id = 4712")
        oldSummary, oldOwner, oldKeywords = c.fetchall()[0]
        c.execute("""SELECT value from ticket_custom
                         where ticket = 4712 and name = 'branch_author'""")
        oldBranchAuthor = c.fetchall()[0][0]
        c.execute("select count(*) from ticket_change where ticket = 4712")
        numComments = c.fetchone()[0]
        d = store.updateTicket('a331422278bd676f3809e7a9d8600647', 4712,
                               updateData)
        def _checkDB(_):
            c.execute(
                "SELECT summary, owner, keywords from ticket where id = 4712")
            self.assertEqual(c.fetchall(),
                             [('awesome ticket', 'jethro', 'review')])
            c.execute("""SELECT time
                               from ticket_change where ticket = 4712
                               order by time desc limit 1""")
            changetime = c.fetchone()[0]
            c.execute("""SELECT author, field, oldvalue, newvalue
                               from ticket_change where ticket = 4712
                               and time = ?""", [changetime])
            self.assertEqual(set(c.fetchall()),
                             set([('alice', 'summary',
                                   oldSummary, updateData['summary']),
                                  ('alice', 'comment',
                                   '20', ''),
                                  ('alice', 'owner',
                                   oldOwner, updateData['owner']),
                                  ('alice', 'keywords',
                                   oldKeywords, updateData['keywords']),
                                  ('alice', 'branch_author',
                                   oldBranchAuthor, updateData['branch_author'])]))
            c.execute("""SELECT value from ticket_custom
                         where ticket = 4712 and name = 'branch_author'""")
            self.assertEqual(c.fetchall(), [('bob',)])
        return d.addCallback(_checkDB)
