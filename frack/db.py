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
        @param runner: A C{norm.interface.IRunner}.
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
                d.addCallback(self._addCustomFields, custom_fields)
            return d
        
        return self.runner.runInteraction(interaction, insert_data, data)


    def _addCustomFields(self, ticket_id, data):
        dlist = []
        for k,v in data.items():
            insert = Insert('ticket_custom', [
                ('ticket', ticket_id),
                ('name', k),
                ('value', v),
            ])
            dlist.append(self.runner.run(insert))
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
        d = defer.gatherResults([normal, custom, comments], consumeErrors=True)
        def combine(results):
            normal, custom, comments = results
            normal.update(custom)
            normal['comments'] = comments
            return normal
        return d.addCallback(combine)
        


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
        for time, author, field, oldvalue, newvalue in changes:
            if time != last:
                comment = {
                    'time': time,
                    'ticket': ticket_number,
                    'author': author,
                    'changes': {}
                }
                ret.append(comment)
            last = time
            if field == 'comment':
                # handle goofy in-reply-to syntax
                number = oldvalue
                if '.' in oldvalue:
                    replyto, number = oldvalue.split('.')
                    comment['replyto'] = replyto

                comment['number'] = number
                comment['comment'] = newvalue
            else:
                comment['changes'][field] = (oldvalue, newvalue)
        return ret


    def updateTicket(self, ticket_number, data, comment):
        """
        Update the attributes of a ticket and maybe add a comment too.
        """
        return self.runner.runInteraction(self._updateTicket, ticket_number,
                                          data, comment)

    def _updateTicket(self, runner, ticket_number, data, comment):
        now = int(time.time())
        ticket = self._fetchTicket(runner, ticket_number)
        fields = ticket.addCallback(self._updateFields, runner, ticket_number,
                                    data, now)
        comment = self._addComment(runner, ticket_number, comment, now)
        return defer.gatherResults([fields, comment])


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


    def _addComment(self, runner, ticket_number, comment, now):
        # get id for new comment
        op = SQL('''
            SELECT oldvalue
            FROM ticket_change
            WHERE ticket = ?
                AND field='comment'
                AND oldvalue != ''
            ''', (ticket_number,))
        
        def getnext(number_list):
            ret = 0
            for number in (x[0] for x in number_list):
                # hooray for heterogeneous lists!
                if '.' in number:
                    number = number.split('.')[1]
                ret = max(int(number), ret)
            return ret + 1

        def add(next_id, runner, ticket_number, comment, author, now):
            op = SQL('''
                INSERT INTO ticket_change
                (ticket, time, author, field, oldvalue, newvalue)
                VALUES (?, ?, ?, 'comment', ?, ?)
                ''', (ticket_number, now, author, str(next_id), comment))
            return runner.run(op)

        d = runner.run(op)
        d.addCallback(getnext)
        d.addCallback(add, runner, ticket_number, comment, self.user, now)
        return d




class DBStore(object):
    """
    Abstract access to Trac's SQL database.

    @param connection: A Python DB-API database connection.
    """
    def __init__(self, connection):
        module, self.connection = connection
        if module.paramstyle == 'qmark':
            self.pl = '?'
        else:
            self.pl = '%s'

    def q(self, query):
        """
        Replace ? in SQL strings with the db driver's placeholder.
        """
        return query.replace('?', self.pl)

    def fetchTicket(self, ticketNumber):
        """
        Look up a ticket and its concomitant changes and attachments.
        """
        c = self.connection.cursor()
        c.execute(self.q(
                "SELECT id, type, time, changetime, component, priority, owner,"
                " reporter, cc, status, resolution, summary, description, "
                "keywords FROM ticket WHERE id = ?"), [ticketNumber])
        ticketRow = c.fetchone()
        if not ticketRow:
            return defer.fail(NotFoundError("No such ticket", ticketNumber))
        c.execute(self.q("SELECT time, author, field, oldvalue, newvalue "
                         "FROM ticket_change WHERE ticket = ? ORDER BY time"),
                  [ticketNumber])
        changeFields = ['time', 'author', 'field', 'oldvalue', 'newvalue']
        ticketFields = ["id", "type", "time", "changetime", "component", "priority", "owner",
                        "reporter", "cc", "status", "resolution", "summary",
                        "description", "keywords"]
        changesRow = c.fetchall()
        ticket = dict([(k, v or '') for k, v in zip(ticketFields, ticketRow)])

        c.execute(self.q("SELECT name, value from ticket_custom where name "
                         "in ('branch', 'branch_author', 'launchpad_bug') "
                         "and ticket = ?"),
                  [ticketNumber])
        ticket.update(c.fetchall())
        ticket['attachments'] = []
        ticket['changes'] = []
        for change in changesRow:
            ticket['changes'].append(dict([(k, v or '') for k, v in zip(changeFields, change)]))
        return defer.succeed(ticket)


    def groupComments(self, ticket):
        """
        Group a ticket's changes into comments.

        @return: The same C{ticket} dictionary with a new C{'comments'}
            item.  Yes, this modifies the passed-in ticket.
        """
        comments = []
        current = {}
        last_time = None
        for change in ticket['changes']:
            if change['time'] != last_time:
                last_time = change['time']
                current = {
                    'time': last_time,
                    'changes': [],
                    'number': str(len(comments)+1),
                    'replyto': None,
                    'comment': '',
                }
                comments.append(current)
            if change['field'] == 'comment':
                current['author'] = change['author']
                current['comment'] = change['newvalue']
                if '.' in change['oldvalue']:
                    current['replyto'] = change['oldvalue'].split('.')[0]
            current['changes'].append(change)
        ticket['comments'] = comments
        return ticket


    def lookupByEmail(self, email):
        """
        Find a username by looking up the associated email address.
        """
        c = self.connection.cursor()
        # check session_attribute for a session associated with email
        c.execute(self.q("SELECT sid from session_attribute "
                         "where name = 'email' and authenticated = 1 "
                                               "and value = ?"), (email,))
        result = c.fetchall()
        if not result:
            username = email
            c.execute(self.q("DELETE FROM session where sid = ?"), (email,))
            c.execute(
                self.q("INSERT INTO session (sid, authenticated, last_visit) "
                       "VALUES (?, ?, ?)"), (email, 1, time.time()))
            c.execute(self.q("INSERT INTO session_attribute "
                             "(sid, authenticated, name, value) "
                             "VALUES (?, ?,'email', ?)"),
                      (email, 1, email))
            self.connection.commit()
        else:
            username = result[0][0]
        c.execute(self.q("SELECT cookie from auth_cookie where name = ?"),
                  (username,))
        result = c.fetchall()
        if not result:
            key = hashlib.sha1(os.urandom(16)).hexdigest()
            c.execute(self.q("INSERT INTO auth_cookie VALUES (?, ?, '', ?)"),
                      (key, username, int(time.time())))
            self.connection.commit()
        else:
            key = result[0][0]
        return defer.succeed((key, username))


    def _auth(self, key):
        c = self.connection.cursor()
        c.execute(self.q("SELECT name from auth_cookie where cookie = ?"),
                  (key,))
        data = c.fetchall()
        if not data:
            return None
        else:
            return data[0][0]

    def updateTicket(self, key, id, data):
        """
        Change a ticket's fields and add to its change log.
        """
        customfields =  ('branch', 'branch_author', 'launchpad_bug')
        fields = ('type', 'component', 'priority', 'owner', 'reporter',
                  'cc', 'status', 'resolution', 'summary', 'description',
                  'keywords')
        comment = data.get('comment')
        customdata = dict((k, v) for (k, v) in data.iteritems()
                          if k in customfields
                             and v is not None)
        data = dict((k, v) for (k, v) in data.iteritems() if k in fields
                                                             and v is not None)
        username = self._auth(key)
        if not username:
            return defer.fail(UnauthorizedError())
        try:
            c = self.connection.cursor()
            c.execute(self.q("SELECT %s from ticket where id = ?"
                             % (','.join(data.keys()),)),
                      (id,))
            oldversion = dict(zip(data.keys(), c.fetchone()))
            c.execute(self.q("SELECT name, value from ticket_custom where ticket = ?"),
                      (id,))
            bits = c.fetchall()
            oldversion.update(dict.fromkeys(customfields, ''))
            oldversion.update(bits)
            t = time.time()
            c.execute(self.q("UPDATE ticket SET %s, changetime=? WHERE id = ?"
                             % ','.join(k + "=?" for k in data)),
                      data.values() + [t, id])
            changes = data.copy()
            changes.update(customdata)
            for k in changes:
                if oldversion[k] != changes[k]:
                    c.execute(self.q("""INSERT INTO ticket_change
                                   (ticket, time, author, field, oldvalue, newvalue)
                                   VALUES (?, ?, ?, ?, ?, ?)"""),
                              [id, t, username, k, oldversion[k], changes[k]])

            for k in customdata:
                if customdata[k] != oldversion[k]:
                    c.execute(self.q("""UPDATE ticket_custom SET value=?
                                    WHERE ticket=? and name=?"""),
                              (customdata[k], id, k))
                    c.execute(self.q("""INSERT INTO ticket_custom
                                    (value, ticket, name)
                                    SELECT ?, ?, ? WHERE NOT EXISTS
                                   (SELECT 1 FROM ticket_custom WHERE ticket=?
                                                                AND name=?)"""),
                              (customdata[k], id, k, id, k))

            c.execute(self.q("""SELECT max(CAST (oldvalue AS float))
                                    from ticket_change where ticket=?
                                                         and field='comment'
                                                         and oldvalue != ''"""),
                      (id,))
            lastcommentnum = int(c.fetchone()[0])
            c.execute(self.q("""INSERT INTO ticket_change
                                (ticket, time, author, field, oldvalue, newvalue)
                                VALUES (?, ?, ?, 'comment', ?, ?)"""),
                      [id, t, username, lastcommentnum, comment or ''])
            self.connection.commit()
        except:
            self.connection.rollback()
            raise
        return defer.succeed(None)
