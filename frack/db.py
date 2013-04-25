# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
import time, hashlib, os
from twisted.internet import defer
from norm.operation import Insert, SQL

class UnauthorizedError(Exception):
    """
    The given key wasn't acceptable for the requested operation.
    """


class NotFoundError(Exception):
    """
    The requested thing was not found.
    """


class Collision(Exception):
    """
    If something is already occupying the space you want.
    """


def postgres_probably_connect(name, username):
    """
    Connect to postgres or die trying.
    """
    try:
        import pgdb
    except ImportError:
        try:
            import psycopg2
        except ImportError:
            from pg8000 import pg8000_dbapi
            module = pg8000_dbapi
            con = pg8000_dbapi.connect(username, host='localhost', database=name)
        else:
            module = psycopg2
            con = psycopg2.connect(host="/var/run/postgresql", database=name,  user=username)
    else:
        module = pgdb
        con = pgdb.connect(host="127.0.0.1", database=name, user=username)
    return module, con


def sqlite_connect(path):
    import sqlite3
    return sqlite3, sqlite3.connect(path)



class TicketStore(object):
    """
    Abstract, authenticated access to Trac's ticket tables.
    """

    editable_columns = ['type', 'component', 'severity',
                   'priority', 'owner', 'cc', 'version',
                   'milestone', 'status', 'resolution', 'summary',
                   'description', 'keywords']

    def __init__(self, runner, user):
        """
        @param runner: A C{norm.interface.IRunner} (which is how I connect to
            the database).
        @param user: string name of user to use as reporter when creating
            tickets and as author when commenting/updating tickets.
        """
        self.runner = runner
        self.user = user


    def createTicket(self, data):
        """
        Create a ticket.

        @param data: A dictionary of data.  The keys are a secret.  You can't
            know them.

        @return: A C{Deferred} which will fire with the newly-created ticket id.
        """
        if not self.user:
            return defer.fail(UnauthorizedError(
                    "You must be logged in to create tickets"))

        if data.get('status', None):
            return defer.fail(Exception("Status must be new"))

        now = int(time.time())
        
        # normal fields
        insert_data = [
            ('reporter', self.user),
            ('time', now),
            ('changetime', now),
            ('status', 'new'),
            ('summary', data['summary']),
        ]
        for column in self.editable_columns:
            insert_data.append((column, data.pop(column, None)))
        
        def interaction(runner, insert_data, custom_fields):
            d = runner.run(Insert('ticket', insert_data, lastrowid=True))
            if custom_fields:
                d.addCallback(self._addCustomFields, custom_fields, runner)
            return d
        
        return self.runner.runInteraction(interaction, insert_data, data)


    def _addCustomFields(self, ticket_id, data, runner):
        dlist = []
        for k,v in data.items():
            insert = Insert('ticket_custom', [
                ('ticket', ticket_id),
                ('name', k),
                ('value', v),
            ])
            dlist.append(runner.run(insert))
        d = defer.gatherResults(dlist, consumeErrors=True)
        return d.addCallback(lambda _:ticket_id)


    def fetchTicket(self, ticket_number):
        """
        Get the normal and custom columns for a ticket and all the comments.

        @return: A Deferred which fires back with a dict.
        """
        return self.runner.runInteraction(self._fetchTicket, ticket_number)


    def _fetchTicket(self, runner, ticket_number):
        normal = self._fetchNormalColumns(runner, ticket_number)
        custom = self._fetchCustomColumns(runner, ticket_number)
        comments = self.fetchComments(ticket_number, _runner=runner)
        attachments = self._fetchAttachments(runner, ticket_number)
        d = defer.gatherResults([normal, custom, comments, attachments],
                                consumeErrors=True)
        def combine(results):
            normal, custom, comments, attachments = results
            normal.update(custom)
            normal['comments'] = comments
            normal['attachments'] = attachments
            return normal
        def notfound(errors):
            errors.value.subFailure.trap(NotFoundError)
            return errors.value.subFailure
        return d.addCallback(combine).addErrback(notfound)
        


    def _fetchNormalColumns(self, runner, ticket_number):
        columns = ['id', 'type', 'time', 'changetime', 'component', 'severity',
                   'priority', 'owner', 'reporter', 'cc', 'version',
                   'milestone', 'status', 'resolution', 'summary',
                   'description', 'keywords']
        sql = '''
            SELECT %(columns)s
            FROM ticket
            WHERE id = ?''' % {
                'columns': ','.join(columns),
            }
        select = SQL(sql, (ticket_number,))
        def firstOne(rows):
            if not rows:
                raise NotFoundError(ticket_number)
            row = rows[0]
            return dict(zip(columns, row))
        return runner.run(select).addCallback(firstOne)


    def _fetchCustomColumns(self, runner, ticket_number):
        op = SQL('''
            SELECT name, value
            FROM ticket_custom
            WHERE ticket = ?''', (ticket_number,))
        return runner.run(op).addCallback(dict)


    def fetchComments(self, ticket_number, _runner=None):
        """
        Get a list of the comments associated with a ticket.
        """
        runner = _runner or self.runner
        
        op = SQL('''
            SELECT time, author, field, oldvalue, newvalue
            FROM ticket_change
            WHERE ticket = ?''', (ticket_number,))
        return runner.run(op).addCallback(self._groupComments, ticket_number)


    def _groupComments(self, changes, ticket_number):
        """
        Group a set of changes into a list of comments.
        """
        ret = []
        comment = {}
        last = None
        i = 1
        for time, author, field, oldvalue, newvalue in changes:
            if time != last:
                comment = {
                    'time': time,
                    'ticket': ticket_number,
                    'author': author,
                    'comment': '',
                    'replyto': '',
                    'followups': [],
                    'number': str(i),
                    'changes': {}
                }
                ret.append(comment)
                i += 1
            last = time
            if field == 'comment':
                # handle goofy in-reply-to syntax
                number = oldvalue
                if '.' in oldvalue:
                    replyto, number = oldvalue.split('.')
                    comment['replyto'] = replyto
                    original = ret[int(replyto)-1]
                    original['followups'].append(number)


                comment['number'] = number
                comment['comment'] = newvalue
            else:
                comment['changes'][field] = (oldvalue, newvalue)
        return ret


    def updateTicket(self, ticket_number, data, comment=None, replyto=None):
        """
        Update the attributes of a ticket and maybe add a comment too.

        @param data: A dict of data.
        @param comment: String comment if there is one
        @param replyto: The comment number to which this comment is a reply.
            Should be an integer >= 1.

        @return: undefined... don't depend on it (except that errback means
            something didn't work)
        """
        if not self.user:
            return defer.fail(UnauthorizedError())
        return self.runner.runInteraction(self._updateTicket, ticket_number,
                                          data, comment or '', replyto)

    def _updateTicket(self, runner, ticket_number, data, comment, replyto):
        now = int(time.time())
        ticket = self._fetchTicket(runner, ticket_number)
        fields = ticket.addCallback(self._updateFields, runner, ticket_number,
                                    data, now)
        comment = self._addComment(runner, ticket_number, comment, replyto, now)
        d = defer.gatherResults([fields, comment], consumeErrors=True)
        def notfound(errors):
            errors.value.subFailure.trap(NotFoundError)
            return errors.value.subFailure
        return d.addErrback(notfound)


    def _updateFields(self, old_ticket, runner, ticket_number, data, now):
        # normal fields
        dlist = []
        set_parts = []
        args = []
        for column in self.editable_columns:
            if column not in data:
                continue
            set_parts.append('%s=?' % (column,))
            newvalue = data.pop(column)
            oldvalue = old_ticket[column]
            args.append(newvalue)

            if newvalue != oldvalue:
                op = SQL('''
                    INSERT INTO ticket_change
                    (ticket, time, author, field, oldvalue, newvalue)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (ticket_number, now, self.user, column, oldvalue, newvalue))
                dlist.append(runner.run(op))

        # changetime
        set_parts.append('changetime=?')
        args.append(now)

        args.append(ticket_number)
        op = SQL('''
            UPDATE ticket
            SET %s
            WHERE id = ?
            ''' % (', '.join(set_parts)), tuple(args))
        dlist.append(runner.run(op))

        # custom fields
        for name, newvalue in data.items():
            oldvalue = old_ticket[name]
            op = SQL('''
                UPDATE ticket_custom
                SET value = ?
                WHERE
                    name = ?
                    and ticket = ?''', (newvalue, name, ticket_number))
            dlist.append(runner.run(op))
            if oldvalue != newvalue:
                op = SQL('''
                    INSERT INTO ticket_change
                    (ticket, time, author, field, oldvalue, newvalue)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (ticket_number, now, self.user, name, oldvalue, newvalue))
                dlist.append(runner.run(op))
        return defer.gatherResults(dlist)


    def _addComment(self, runner, ticket_number, comment, replyto, now):
        # get id for new comment
        op = SQL('''
            SELECT oldvalue
            FROM ticket_change
            WHERE ticket = ?
                AND field='comment'
                AND oldvalue != ''
            ''', (ticket_number,))
        
        def getnext(number_list):
            # XXX there is a race condition here.  Two comments could have
            # the same number.
            ret = 0
            for number in (x[0] for x in number_list):
                # hooray for heterogeneous lists!
                if '.' in number:
                    number = number.split('.')[1]
                ret = max(int(number), ret)
            return ret + 1

        def add(next_id, runner, ticket_number, comment, replyto, author, now):
            next_id = str(next_id)
            if replyto:
                next_id = '%s.%s' % (replyto, next_id)
            op = SQL('''
                INSERT INTO ticket_change
                (ticket, time, author, field, oldvalue, newvalue)
                VALUES (?, ?, ?, 'comment', ?, ?)
                ''', (ticket_number, now, author, str(next_id), comment))
            return runner.run(op)

        d = runner.run(op)
        d.addCallback(getnext)
        d.addCallback(add, runner, ticket_number, comment, replyto, self.user, now)
        return d


    def makeDict(self, rows, columns):
        return [dict(zip(columns, x)) for x in rows]


    def fetchComponents(self):
        """
        Get a list of dicts for all the available components.
        """
        op = SQL('''
            SELECT name, owner, description
            FROM component
            ORDER BY name
            ''')
        return self.runner.run(op).addCallback(self.makeDict, ['name', 'owner', 'description'])


    def fetchMilestones(self):
        """
        Get a list of dicts for all the milestones.
        """
        columns = ['name', 'due', 'completed', 'description']
        op = SQL('''
            SELECT %s
            FROM milestone
            ''' % (','.join(columns)))
        return self.runner.run(op).addCallback(self.makeDict, columns)


    def fetchEnum(self, enum_type):
        """
        Get a list of dicts of all the enum key-value pairs for a given type.
        """
        columns = ['name', 'value']
        op = SQL('''
            SELECT %s
            FROM "enum"
            WHERE type = ?
            ''' % (','.join(columns),), (enum_type,))
        return self.runner.run(op).addCallback(self.makeDict, columns)


    def _fetchAttachments(self, runner, ticket_number):
        columns = ['filename', 'size', 'time', 'description', 'author', 'ipnr']
        op = SQL('''
            SELECT %s
            FROM attachment
            WHERE type = 'ticket'
                AND id = ?
            ''' % (','.join(columns),), (ticket_number,))
        d = runner.run(op).addCallback(self.makeDict, columns)
        def addIp(r):
            for x in r:
                x['ip'] = x['ipnr']
            return r
        return d.addCallback(addIp)


    def addAttachmentMetadata(self, ticket_number, data):
        """
        Add attachment metadata to a ticket.

        @param ticket_number: The ticket number (e.g. 1234)
        @param data: a dictionary similar to this::

            {
                'filename': 'something.diff',
                'size': 29930,
                'description': 'file description',
                'ip': '29.33.44.21',
            }
        """
        if not self.user:
            return defer.fail(UnauthorizedError())

        now = int(time.time())
        op = SQL('''
            INSERT INTO attachment
            (type, id, filename, size, "time", description, author, ipnr)
            VALUES ('ticket', ?, ?, ?, ?, ?, ?, ?)
            ''', (ticket_number, data['filename'], data['size'], now,
                  data['description'], self.user, data['ip']))
        return self.runner.run(op)


    def userList(self):
        """
        Get a list of the users in the database.
        """
        # XXX should we check authenticated?
        op = SQL('''
            SELECT sid
            FROM session
            ORDER BY sid''')
        def parseRows(rows):
            return (x[0] for x in rows)
        return self.runner.run(op).addCallback(parseRows)



class AuthStore(object):
    """
    Access to the authentication/session portion of Trac's SQL database.

    @param runner: A C{norm.interface.IRunner} (which how I connect to the 
        database).
    """

    def __init__(self, runner):
        self.runner = runner


    def usernameFromEmail(self, email):
        """
        Translate an email address to a username if possible.

        @param email: The email address.

        @return: A C{Deferred} firing with the username (string) associated
            with the C{email}.  This will errback with L{NotFoundError} if
            there is no association for the email address.
        """
        op = SQL('''
            SELECT sid
            FROM session_attribute
            WHERE
                name = 'email'
                AND authenticated = ?
                AND value = ?''', (True, email))
        def parseRows(rows):
            if not rows:
                raise NotFoundError('No username for email %r' % (email,))
            return rows[0][0]
        return self.runner.run(op).addCallback(parseRows)


    def createUser(self, email, username=None):
        """
        Create a "user" with an associated email address.

        @param email: An email address.
        @param username: The username to use.  If C{None} is provided, the
            C{email} will be used as the username.

        @return: A C{Deferred} firing with C{username} on success.
        """
        username = username or email

        @defer.inlineCallbacks
        def interaction(runner, email, username):            
            # make sure there's no association of the email address with a 
            # different username
            rows = yield runner.run(SQL(
                "SELECT sid "
                "FROM session_attribute "
                "WHERE "
                    "sid <> ? "
                    "AND authenticated = ? "
                    "AND name = ? "
                    "AND value = ?", (username, True, u'email', email)
            ))
            if rows:
                raise Collision(username)

            _ = yield runner.run(SQL(
                "INSERT INTO session "
                "(sid, authenticated, last_visit) "
                "VALUES (?, ?, ?)", (username, True, int(time.time()))
            ))
            _ = yield runner.run(SQL(
                "INSERT INTO session_attribute "
                "(sid, authenticated, name, value) "
                "VALUES (?, ?, ?, ?)", (username, True, u'email', email)
            ))
        d = self.runner.runInteraction(interaction, email, username)
        d.addCallback(lambda _: username)

        def eb(err, username):
            # probably an IntegrityError?  What's a better way to do this?
            raise Collision(username)
        d.addErrback(eb, username)

        return d


    def cookieFromUsername(self, username):
        """
        Translate a username into a cookie value, creating it if an existing
        cookie value doesn't already exist.

        @param username: Username to get cookie value for.

        @return: A C{Deferred} which will fire with a cookie value (string).
        """
        op = SQL(
            "SELECT cookie "
            "FROM auth_cookie "
            "WHERE name = ?", (username,)
        )
        def parseRows(rows):
            if not rows:
                value = hashlib.sha1(os.urandom(16)).hexdigest()
                op = SQL(
                    "INSERT INTO auth_cookie "
                    "(cookie, name, ipnr, time) "
                    "VALUES (?, ?, '', ?)", (value, username, int(time.time()))
                )
                return self.runner.run(op).addCallback(lambda _:value)
            return rows[0][0]
        return self.runner.run(op).addCallback(parseRows)


    def usernameFromCookie(self, cookie_value):
        """
        Get the username associated with an authentication cookie's value.

        @param cookie_value: A value returned by L{cookieFromUsername} and
            likely stored in the browser as the C{trac_auth} cookie.

        @return: A C{Deferred} which will fire with a username or will errback
            with C{NotFoundError} if C{cookie_value} is not a valid cookie.
        """
        op = SQL(
            "SELECT name "
            "FROM auth_cookie "
            "WHERE cookie = ?", (cookie_value,)
        )
        def parseRows(rows):
            if not rows:
                raise NotFoundError(cookie_value)
            return rows[0][0]
        return self.runner.run(op).addCallback(parseRows)

