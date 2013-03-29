import sqlite3
import time
from twisted.trial.unittest import TestCase
from twisted.python.util import sibpath
from twisted.internet import defer
from frack.db import (TicketStore, DBStore, UnauthorizedError, NotFoundError,
                      AuthStore, Collision)
from norm.sqlite import SqliteTranslator
from norm.common import BlockingRunner
from norm.operation import SQL



class TicketStoreTest(TestCase):


    def populatedStore(self):
        db = sqlite3.connect(":memory:")
        db.executescript(open(sibpath(__file__, "trac_test.sql")).read())
        translator = SqliteTranslator()
        runner = BlockingRunner(db, translator)
        store = TicketStore(runner, user='foo')
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
        self.assertEqual(ticket['attachments'], [])


    def test_createTicket_status(self):
        """
        You can't override the status of a ticket while creating it.
        """
        store = self.populatedStore()

        self.assertFailure(store.createTicket({
            'summary': 'something',
            'status': 'something',
        }), Exception)


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
    def test_createTicket_customFields_fail(self):
        """
        If the custom fields can't be created, the whole transaction should be
        rolled back and the ticket should not be added.
        """
        store = self.populatedStore()

        count = yield store.runner.run(SQL('select count(*) from ticket'))

        bad_data = {
            'summary': 'good summary',
            'branch': object(),
        }
        try:
            yield store.createTicket(bad_data)
        except:
            pass
        else:
            self.fail("Should have raised an exception")

        after_count = yield store.runner.run(SQL('select count(*) from ticket'))
        self.assertEqual(count, after_count, "Should NOT have created a ticket")


    def test_createTicket_noauth(self):
        """
        Unauthenticated users can't create tickets
        """
        store = self.populatedStore()
        store.user = None

        self.assertFailure(store.createTicket({
            'summary': 'good summary',
        }), UnauthorizedError)


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

        # comments
        self.assertEqual(len(ticket['comments']), 4)

        # attachments
        self.assertEqual(len(ticket['attachments']), 0)


    @defer.inlineCallbacks
    def test_fetchTicket_attachments(self):
        """
        Attachment metadata should be included when fetching a ticket.
        """
        store = self.populatedStore()

        ticket = yield store.fetchTicket(5517)

        self.assertEqual(ticket['attachments'], [
            {
                'filename': '5517.diff',
                'size': 3472,
                'time': 1331531954,
                'description': '',
                'author': 'candre717',
                'ip': '66.35.39.65',
                # for compatibility?
                'ipnr': '66.35.39.65',
            }
        ])


    def test_dne(self):
        """
        Should fail appropriately if the ticket doesn't exist.
        """
        store = self.populatedStore()

        self.assertFailure(store.fetchTicket(1), NotFoundError)
        self.assertFailure(store.updateTicket(1, {}), NotFoundError)


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
        self.assertEqual(c['changes']['branch'], ('', 'branches/tcp-endpoints-tests-refactor-5622'))
        self.assertEqual(c['changes']['branch_author'], ('', 'exarkun'))


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


    @defer.inlineCallbacks
    def test_fetchComments_all(self):
        """
        All comments should have a comments item, even if it's blank.
        """
        store = self.populatedStore()

        comments = yield store.fetchComments(4712)
        for i,c in enumerate(comments):
            self.assertTrue('comment' in c, c)
            self.assertEqual(c['number'], str(i+1))


    @defer.inlineCallbacks
    def test_updateTicket(self):
        """
        You can update attributes of a ticket while making a comment
        """
        store = self.populatedStore()

        data = {
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
            'branch': 'foo',
            'launchpad_bug': '1234',
        }
        comment = 'this is my new comment'

        yield store.updateTicket(5622, data, comment)
        ticket = yield store.fetchTicket(5622)
        for k, v in data.items():
            self.assertEqual(ticket[k], v,
                "Expected ticket[%r] to be %r, not %r" % (k, v, ticket[k]))

        self.assertEqual(ticket['comments'][-1]['comment'],
                         'this is my new comment', "Should add a comment")
        self.assertEqual(ticket['comments'][-1]['number'], '5')
        self.assertEqual(ticket['comments'][-1]['author'], 'foo')
        self.assertEqual(ticket['comments'][-1]['ticket'], 5622)
        self.assertEqual(ticket['comments'][-1]['time'], ticket['changetime'])
        self.assertEqual(ticket['comments'][-1]['replyto'], '')
        self.assertEqual(ticket['comments'][-1]['followups'], [])

        # every change should be recorded, too
        changes = ticket['comments'][-1]['changes']

        # these magical values come from trac_test.sql
        expected_changes = [
            ('type', 'enhancement', 'type'),
            ('component', 'core', 'component'),
            ('severity', None, 'severity'),
            ('priority', 'normal', 'priority'),
            ('owner', '', 'owner'),
            # reporter
            ('cc', '', 'cc'),
            ('version', None, 'version'),
            ('milestone', '', 'milestone'),
            ('status', 'closed', 'status'),
            ('resolution', 'duplicate', 'resolution'),
            # summary and description tested separately
            ('branch', 'branches/tcp-endpoints-tests-refactor-5622',
                'foo'),
            ('launchpad_bug', '', '1234'),
        ]
        for field, old, new in expected_changes:
            expected = (old, new)
            actual = changes[field]
            self.assertEqual(actual, expected, "Expected %r change to"
                             " be %r, not %r" % (field, expected, actual))

        # summary and description are long an obnoxious to duplicate in the code
        self.assertEqual(changes['summary'][1], 'summary')
        self.assertEqual(changes['description'][1], 'description')


    def test_updateTicket_noauth(self):
        """
        If you are not authenticated, you can't update tickets
        """
        store = self.populatedStore()

        store.user = None
        self.assertFailure(store.updateTicket(5622, {}),
                           UnauthorizedError)


    @defer.inlineCallbacks
    def test_updateTicket_noComment(self):
        """
        If there's no comment, that's okay.
        """
        store = self.populatedStore()

        yield store.updateTicket(5622, dict(type='type'))
        ticket = yield store.fetchTicket(5622)
        self.assertEqual(ticket['comments'][-1]['comment'], '')
        self.assertEqual(ticket['comments'][-1]['changes']['type'],
                         ('enhancement', 'type'))



    @defer.inlineCallbacks
    def test_updateTicket_reply(self):
        """
        You can signal that a comment is in reply to another comment
        """
        store = self.populatedStore()

        yield store.updateTicket(5622, {}, comment='something', replyto=1)
        ticket = yield store.fetchTicket(5622)
        comment = ticket['comments'][-1]
        self.assertEqual(comment['comment'], 'something')
        self.assertEqual(comment['replyto'], '1')

        original = ticket['comments'][0]
        self.assertEqual(original['followups'], ['5'], "Should know which "
                         "comments are followups to it")


    @defer.inlineCallbacks
    def test_updateTicket_onlyLogChanges(self):
        """
        Only fields that have actually changed should be logged
        """
        store = self.populatedStore()

        data = {
            'type': 'enhancement',
            'component': 'new component',
        }

        yield store.updateTicket(5622, data)
        ticket = yield store.fetchTicket(5622)

        changes = ticket['comments'][-1]['changes']
        self.assertEqual(changes['component'], ('core', 'new component'))
        self.assertEqual(len(changes), 1, "Should only log the component")


    @defer.inlineCallbacks
    def test_fetchComponents(self):
        """
        Should get all the values in the component table.
        """
        store = self.populatedStore()

        components = yield store.fetchComponents()
        self.assertEqual(components, [
            {'name': 'conch', 'owner': '', 'description': ''},
            {'name': 'core', 'owner': '', 'description': ''},
            {'name': 'ftp', 'owner': '', 'description': ''},
        ])


    @defer.inlineCallbacks
    def test_fetchMilestones(self):
        """
        Should get all the milestones available.
        """
        store = self.populatedStore()

        milestones = yield store.fetchMilestones()
        self.assertEqual(len(milestones), 4)
        self.assertIn({
            'name': 'not done, not due',
            'due': None,
            'completed': None,
            'description': 'description',
        }, milestones)


    @defer.inlineCallbacks
    def test_fetchEnum(self):
        """
        Should get all the enums in the db.
        """
        store = self.populatedStore()

        priorities = yield store.fetchEnum('priority')
        self.assertEqual(priorities, [
            {'name': 'drop everything', 'value': ''},
            {'name': 'normal', 'value': ''},
        ])


    @defer.inlineCallbacks
    def test_addAttachmentMetadata(self):
        """
        You can add attachment metadata to a ticket.
        """
        store = self.populatedStore()

        now = int(time.time())

        yield store.addAttachmentMetadata(5622, {
            'filename': 'the file',
            'size': 1234,
            'description': 'this is a description',
            'ip': '127.0.0.1',
        })
        ticket = yield store.fetchTicket(5622)
        self.assertEqual(len(ticket['attachments']), 1)
        att = ticket['attachments'][0]
        self.assertEqual(att['filename'], 'the file')
        self.assertEqual(att['size'], 1234)
        self.assertEqual(att['description'], 'this is a description')
        self.assertEqual(att['ip'], '127.0.0.1')
        self.assertEqual(att['ipnr'], '127.0.0.1')
        self.assertTrue(att['time'] >= now)
        self.assertEqual(att['author'], 'foo')


    def test_addAttachmentMetadata_noauth(self):
        """
        If you are not authenticated, you can't upload.
        """
        store = self.populatedStore()

        store.user = None
        self.assertFailure(store.addAttachmentMetadata(5622, {}),
                           UnauthorizedError)



class AuthStoreTest(TestCase):
    """
    Tests for database-backed authentication.
    """

    def populatedStore(self):
        """
        Return an L{AuthStore} with some expected user data in it.
        """
        db = sqlite3.connect(":memory:")
        db.executescript(open(sibpath(__file__, "trac_test.sql")).read())
        translator = SqliteTranslator()
        runner = BlockingRunner(db, translator)
        store = AuthStore(runner)
        return store


    @defer.inlineCallbacks
    def test_usernameFromEmail(self):
        """
        usernameFromEmail should translate an email address to a username if
        possible, otherwise, it should raise an exception.
        """
        store = self.populatedStore()

        username = yield store.usernameFromEmail('alice@example.com')
        self.assertEqual(username, 'alice')

        self.assertFailure(store.usernameFromEmail('dne@example.com'),
                           NotFoundError)


    @defer.inlineCallbacks
    def test_createUser(self):
        """
        createUser will create a user associated with an email address
        """
        store = self.populatedStore()

        username = yield store.createUser('joe@example.com', 'joe')
        self.assertEqual(username, 'joe', "Should return the username")

        username = yield store.usernameFromEmail('joe@example.com')
        self.assertEqual(username, 'joe')


    @defer.inlineCallbacks
    def test_createUser_justEmail(self):
        """
        You can provide just the email address
        """
        store = self.populatedStore()

        username = yield store.createUser('joe@example.com')
        self.assertEqual(username, 'joe@example.com')

        username = yield store.usernameFromEmail('joe@example.com')
        self.assertEqual(username, 'joe@example.com')


    def test_createUser_alreadyExists(self):
        """
        When trying to create a user with the same username as another user,
        an error is returned.  Also, if the email address is being used, it's
        an error too.
        """
        store = self.populatedStore()

        self.assertFailure(store.createUser('alice@example.com', 'alice'),
                           Collision)

        # email associated with more than one user is not allowed
        self.assertFailure(store.createUser('alice@example.com', 'bob'),
                           Collision)


    @defer.inlineCallbacks
    def test_cookieFromUsername(self):
        """
        Should get or create an auth_cookie entry.
        """
        store = self.populatedStore()

        cookie_value = yield store.cookieFromUsername('alice')

        # this magical value is found in test/trac_test.sql
        self.assertEqual(cookie_value, "a331422278bd676f3809e7a9d8600647",
                         "Should match the existing cookie value")

        username = yield store.createUser('joe@example.com')
        cookie_value = yield store.cookieFromUsername(username)
        self.assertNotEqual(cookie_value, None)
        value2 = yield store.cookieFromUsername(username)
        self.assertEqual(cookie_value, value2)


    @defer.inlineCallbacks
    def test_usernameFromCookie(self):
        """
        Should return the username associated with a cookie value.
        """
        store = self.populatedStore()

        alice_cookie = "a331422278bd676f3809e7a9d8600647"
        username = yield store.usernameFromCookie(alice_cookie)
        self.assertEqual(username, 'alice')

        self.assertFailure(store.usernameFromCookie('dne'), NotFoundError)



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
        c.fetchone()[0]
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
