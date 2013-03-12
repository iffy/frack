import sqlite3
from twisted.trial.unittest import TestCase
from twisted.python.util import sibpath
from twisted.internet import defer
from frack.db import TicketStore, DBStore, UnauthorizedError, NotFoundError
from norm.sqlite import SqliteSyncTranslator
from norm.common import Executor, SyncRunner



class TicketStoreTest(TestCase):


    def populatedStore(self):
        db = sqlite3.connect(":memory:")
        db.executescript(open(sibpath(__file__, "trac_test.sql")).read())
        translator = SqliteSyncTranslator()
        runner = SyncRunner(db)
        executor = Executor(translator, runner)
        store = TicketStore(executor, user='foo')
        return store


    @defer.inlineCallbacks
    def test_createTicket_minimal(self):
        """
        You can create tickets
        """
        store = self.populatedStore()
        # a minimal ticket
        data = {
            'summary': 'the summary',
            }
        ticket_id = yield store.createTicket(data)
        self.assertNotEqual(ticket_id, None,
            "Should return the new id: %s" % (ticket_id,))

        ticket = yield store.fetchTicket(ticket_id)
        # Assert for each of the fields:
        # http://trac.edgewall.org/wiki/TracDev/DatabaseSchema/TicketSystem#Tableticket
        # XXX should these be '' instead of None?
        self.assertEqual(ticket['id'], ticket_id)
        self.assertEqual(ticket['type'], None)
        self.assertTrue(ticket['time'])
        self.assertTrue(ticket['changetime'])
        self.assertEqual(ticket['time'], ticket['changetime'])

        self.assertEqual(ticket['component'], None)
        self.assertEqual(ticket['severity'], None)
        self.assertEqual(ticket['priority'], None)
        self.assertEqual(ticket['owner'], None)
        self.assertEqual(ticket['reporter'], 'foo', "Should use the Store's "
                         "user as the report")
        self.assertEqual(ticket['cc'], None)
        self.assertEqual(ticket['version'], None)
        self.assertEqual(ticket['milestone'], None)
        self.assertEqual(ticket['status'], 'new')
        self.assertEqual(ticket['resolution'], None)
        self.assertEqual(ticket['summary'], 'the summary')
        self.assertEqual(ticket['description'], None)
        self.assertEqual(ticket['keywords'], None)


    @defer.inlineCallbacks
    def test_createTicket_maximal(self):
        """
        You can create a ticket with all kinds of options.
        """
        store = self.populatedStore()
        # Do I need to enforce that all the values are valid options in their
        # specific join tables?
        data = {
            # do I need to enforce that this is in enum type=ticket_type? 
            'type': 'type',
            'component': 'component',
            'severity': 'severity',
            'priority': 'priority',
            'owner': 'owner',
            'cc': 'cc',
            'version': 'version',
            'milestone': 'milestone',
            'status': 'status',
            'resolution': 'resolution',
            'summary': 'summary',
            'description': 'description',
            'keywords': 'keywords',
            }
        ticket_id = yield store.createTicket(data)
        ticket = yield store.fetchTicket(ticket_id)
        
        self.assertEqual(ticket['id'], ticket_id)
        self.assertEqual(ticket['type'], 'type')
        self.assertTrue(ticket['time'])
        self.assertTrue(ticket['changetime'])
        self.assertEqual(ticket['time'], ticket['changetime'])

        self.assertEqual(ticket['component'], 'component')
        self.assertEqual(ticket['severity'], 'severity')
        self.assertEqual(ticket['priority'], 'priority')
        self.assertEqual(ticket['owner'], 'owner')
        self.assertEqual(ticket['reporter'], 'foo', "Should use the Store's "
                         "user as the report")
        self.assertEqual(ticket['cc'], 'cc')
        self.assertEqual(ticket['version'], 'version')
        self.assertEqual(ticket['milestone'], 'milestone')
        self.assertEqual(ticket['status'], 'new')
        self.assertEqual(ticket['resolution'], 'resolution')
        self.assertEqual(ticket['summary'], 'summary')
        self.assertEqual(ticket['description'], 'description')
        self.assertEqual(ticket['keywords'], 'keywords')


    @defer.inlineCallbacks
    def test_createTicket_customFields(self):
        """
        You can create a ticket with custom fields
        """
        store = self.populatedStore()

        data = {
            'branch': 'foo',
            'summary': 'something',
            'launchpad_bug': '1234',
        }
        ticket_id = yield store.createTicket(data)
        ticket = yield store.fetchTicket(ticket_id)

        self.assertEqual(ticket['branch'], 'foo')
        self.assertEqual(ticket['summary'], 'something')
        self.assertEqual(ticket['launchpad_bug'], '1234')


    @defer.inlineCallbacks
    def test_fetchTicket(self):
        """
        You can fetch existing ticket information
        """
        store = self.populatedStore()

        ticket = yield store.fetchTicket(5622)

        # look in test/trac_test.sql to see the values
        self.assertEqual(ticket['id'], 5622)
        self.assertEqual(ticket['type'], 'enhancement')
        self.assertEqual(ticket['time'], 1333844383)
        self.assertEqual(ticket['changetime'], 1334260992)
        self.assertEqual(ticket['component'], 'core')
        self.assertEqual(ticket['severity'], None)
        self.assertEqual(ticket['priority'], 'normal')
        self.assertEqual(ticket['owner'], '')
        self.assertEqual(ticket['reporter'], 'exarkun')
        self.assertEqual(ticket['cc'], '')
        self.assertEqual(ticket['version'], None)
        self.assertEqual(ticket['milestone'], '')
        self.assertEqual(ticket['status'], 'closed')
        self.assertEqual(ticket['resolution'], 'duplicate')
        # ignore summary and description because they're long
        self.assertEqual(ticket['keywords'], 'tests')

        # custom fields
        self.assertEqual(ticket['branch'], 'branches/tcp-endpoints-tests-refactor-5622')
        self.assertEqual(ticket['branch_author'], 'exarkun')
        self.assertEqual(ticket['launchpad_bug'], '')


    @defer.inlineCallbacks
    def test_fetchComments(self):
        """
        You can get all the comments for a ticket.
        """
        store = self.populatedStore()

        comments = yield store.fetchComments(5622)

        # look in test/trac_test.sql to see where these assertions come from
        self.assertEqual(len(comments), 4, "There are 4 comments")
        c = comments[0]
        self.assertEqual(c['ticket'], 5622)
        self.assertEqual(c['time'], 1333844456)
        self.assertEqual(c['author'], 'exarkun')
        self.assertEqual(c['number'], '1')
        self.assertEqual(c['comment'], "(In [34131]) Branching to 'tcp-endpoints-tests-refactor-5622'")
        self.assertEqual(len(c['changes']), 2)
        self.assertIn({
            'field': 'branch',
            'oldvalue': '',
            'newvalue': 'branches/tcp-endpoints-tests-refactor-5622',
        }, c['changes'])
        self.assertIn({
            'field': 'branch_author',
            'oldvalue': '',
            'newvalue': 'exarkun',
        }, c['changes'])


    @defer.inlineCallbacks
    def test_fetchComments_reply(self):
        """
        The comments should know that they are a reply to another comment
        """
        store = self.populatedStore()

        comments = yield store.fetchComments(2723)

        # look in test/trac_test.sql to see where these assertions come from
        comment13 = comments[12]
        self.assertEqual(comment13['replyto'], '12')
        self.assertEqual(comment13['number'], '13')



class DBStoreTest(TestCase):
    """
    Tests for database-backed ticket storage/retrieval.
    """

    def setUp(self):
        # test with an sqlite database
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


    def test_groupComments(self):
        """
        You can grouped changes into related comments.
        """
        store = DBStore((sqlite3, self.db))
        d = store.fetchTicket(4712)
        d.addCallback(store.groupComments)
        def _check(result):
            self.assertEqual(set(result.keys()),
                             set(["type", "status", "summary", "time", "reporter",
                              "owner", "priority",  "resolution", "component",
                              "keywords", "cc", "branch", "branch_author",
                              "launchpad_bug", "description", "changes",
                              "attachments", "id", "changetime", "comments"]))

            self.assertEqual(len(result['comments']), 21)
            self.assertEqual([x['number'] for x in result['comments']],
                             map(str,range(1,22)))

            comment = result['comments'][0]
            self.assertEqual(comment['author'], 'cyli')
            self.assertEqual(comment['time'], 1288021673)
            self.assertEqual(comment['number'], '1')
            self.assertEqual(len(comment['changes']), 2)
            self.assertEqual(set(comment['changes'][0].keys()),
                             set(["newvalue", "author", "oldvalue", "time", "field"]))

            self.assertEqual(result['comments'][13]['replyto'], '12', "Should "
                             "know about replies to comments")

        return d.addCallback(_check)        


    def test_fetchTicket_dne(self):
        """
        `fetchTicket` will errback if the ticket doesn't exist.
        """
        store = DBStore((sqlite3, self.db))
        d = store.fetchTicket(1000000)
        def _cb(result):
            self.fail("Should have errbacked with NotFoundError: %r" % (result,))
        def _eb(result):
            result.trap(NotFoundError)
        return d.addCallbacks(_cb, _eb)


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
