BEGIN TRANSACTION;
CREATE TABLE ticket (id integer not null primary key, type text, time int, changetime int, component text, severity text, priority text, owner text, reporter text, cc text, version text, milestone text, status text, resolution text, summary text, description text, keywords text);
INSERT INTO "ticket" VALUES(3312,'defect',1214395506,1332115134,'core',NULL,'highest','stupidInvaders','stupidInvaders','exarkun',NULL,'','closed','fixed','Silent server crash with kqueue.reactor','While high loaded, with ~1000 clients, server silently crashes. Crash looks like: 
server seems to be working but clients can''t join the server.At that there no errors in stderr and logs.
We may possibly have an error in our code. Everything was made according to manuals.

We use: FreeBSD 6.1 and 7.0; python2.4; twisted 8.1 and twisted 2.5.

{{{
import sys
import time
import md5

if "freebsd" in sys.platform:
    from twisted.internet import kqreactor
    kqreactor.install()
elif "linux" in sys.platform:
    from twisted.internet import epollreactor
    epollreactor.install()

from twisted.internet import protocol
from twisted.internet import reactor
#required for using threads with the Reactor
from twisted.python import threadable
threadable.init()

class Protocol(protocol.Protocol):
    """ClientProtocol"""
    data = ""
    maxConnections = 5000

    def connectionMade(self):
        self.factory.countConnections += 1
        if self.factory.countConnections > self.maxConnections:
            """Too many connections, try later"""
            self.transport.loseConnection()

    def connectionLost(self, reason):
        self.factory.countConnections -= 1
        self.transport.loseConnection()

    def dataReceived(self, data):
        """As soon as any data is received, write it back."""
        self.data = self.data + data
        self.parseCommand()

    def parseCommand(self):
        """Must be overridden"""
        self.handleCommand()
        
    def handleCommand(self):
        """Must be overridden"""
        response = ""
        self.sendResponse(response)

    def sendResponse(self, response):
        """Must be overridden"""
        msg = self.data
        print msg
        self.transport.write(msg)   
        
class ClientFactory(protocol.ClientFactory):
    """ClientFactory"""
    countConnections = 0
    clients = {}

    def __init__(self, pr = Protocol):
        self.protocol = pr
    
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed:", reason
        
class ReconnectingClientFactory(protocol.ReconnectingClientFactory):
    """ReconnectingClientFactory"""
    def __init__(self, pr = Protocol):
        self.protocol = pr
        self.initialDelay = 1
        self.delay = self.initialDelay
        self.maxDelay = 60
        self.factor = 1

    def clientConnectionLost(self, connector, reason):
        print "Lost connection. Reason:", reason
        time.sleep(self.delay)
        self.delay *=  self.factor
        if self.delay > self.maxDelay:
            self.delay = self.maxDelay
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed. Reason:", reason
        time.sleep(self.delay)
        self.delay *=  self.factor
        if self.delay > self.maxDelay:
            self.delay = self.maxDelay
        connector.connect()
    
class Server(object):
    """Server"""
    protocols = {}
    
    def __init__(self, listeningPorts = {}, connectingPorts = {}):
        self.listeningPorts = listeningPorts
        self.connectingPorts = connectingPorts
        self.factories = {}
        # Множество слушающих портов
        for item in self.listeningPorts.iteritems():
            protocolID = item[0]
            protocol = self.protocols[protocolID]
            factory = ClientFactory(protocol)
            self.factories[protocolID] = factory
        # Множество коннектящихся портов
        for item in self.connectingPorts.iteritems():
            protocolID = item[0]
            protocol = self.protocols[protocolID]
            factory = ReconnectingClientFactory(protocol)
            self.factories[protocolID] = factory            
        
    def __del__(self):
        pass
        
    def start(self):
        """Start the server"""
        self.__reactor = reactor
        self.__listener = {}
        self.__connector = {}
        for item in self.listeningPorts.iteritems():
            protocolID = item[0]
            protocol = self.protocols[protocolID]
            host, port = item[1]
            self.__listener[protocolID] = self.__reactor.listenTCP(port, self.factories[protocolID])
        for item in self.connectingPorts.iteritems():
            protocolID = item[0]
            protocol = self.protocols[protocolID]
            host, port = item[1]
            self.__connector[protocolID] = self.__reactor.connectTCP(host, port, self.factories[protocolID],timeout=0.5)
        self.__reactor.run(installSignalHandlers=0)
        
    def stop(self):
        """Correct way to stop the server"""
        self.__reactor.stop()

    def crash(self):
        """Crash the server. Data may be lost"""
        for protocolID in self.listeningPorts.iterkeys():
            self.__listener[protocolID].connectionLost("")
        for protocolID in self.connectingPorts.iterkeys():
            self.__listener[protocolID].connectionLost("")
        self.__reactor.crash()
        
    def cold_restart(self):
        """May be overridden"""
        
    def soft_restart(self):
        """May be overridden"""
        
    def hard_restart(self):
        """May be overridden"""

    def status(self):
        """Server status (running or not)"""
        return self.__reactor.running

}}}
','');
INSERT INTO "ticket" VALUES(5622,'enhancement',1333844383,1334260992,'core',NULL,'normal','','exarkun','',NULL,'','closed','duplicate','Refactor TCPClientTestsBuilder and TCP6ClientTestsBuilder to make their endpoint factories re-usable for other test cases','These two `ReactorBuilder` subclasses also define useful functionality for other test cases, but since they inherit test methods from another `TestCase` mixin, that functionality can''t be re-used without also inheriting those test methods (which at best will cause tests to be run repeatedly, at worst will add unwanted failing tests to another case).
','tests');
INSERT INTO "ticket" VALUES(2723,'enhancement',1182804821,1334367409,'core',NULL,'lowest','glyph','glyph','thijs, jesstess, khorn',NULL,'','new',NULL,'Twisted.Quotes does not serve its original intended purpose','= Problem =

The idea for a Twisted quotefile started with a tradition at Origin, where each released game included a quotefile from the game''s development team.  This allowed the users to get a feel for the developers'' culture, and the developers to feel a bit more connected to the users by sharing it.

At the time I originally thought of having a quote file, I assumed that the Twisted team would simply grow and the team would acquire new members over time; there was no "final release" so one quotefile that just got bigger made sense.

However, the current quotefile has several problems:

  * The default sort order when reading it in an editor or pager - newest quotes last - presents users first with the quotations least relevant to the current release of Twisted.
  * The quotefile is huge, and so readers are overwhelmed by its length and don''t read it as often as they used to.  (I am guessing this just from the amount of off-the-cuff feedback I used to get about the quotefile''s utility and the feedback I get now about its relative incomprehensibility.)
  * The quotefile includes lots of quotes from people who don''t even work on Twisted any more (and in many cases, never worked on Twisted).  Those quotes should''t be removed, since they were perhaps relevant to the hackers'' state of mind at the time, but again... not relevant today.

= Proposed Solution =

The quotefile for a given Twisted release should reflect the culture that produced that release.  The team around Twisted changes with the ebb and flow of different developers'' free time, so I think a good solution here would be to split the quotefile up into several different files, and only include one with each release.

If we ever manage to fix the problem that releases take a really long time, we might want to aggregate them differently, but I think for the time being one file / one release makes sense.','fun, documentation');
INSERT INTO "ticket" VALUES(5517,'task',1331151798,1331576061,'runner',NULL,'low','','thijs','thijs',NULL,'','closed','fixed','Remove deprecated t.r.procmon.ProcessMonitor.active','`ProcessMonitor.active`, `consistencyDelay`, and `consistency` in [source:trunk/twisted/runner/procmon.py] are deprecated since 10.1 and can be removed.

{{{
twisted.runner.test.test_procmon.ProcmonTests.test_activeAttributeEqualsRunning ... [OK]
/home/buildbot/twisted/slave.trunk/fedora11-64bit-py2.7/Twisted/twisted/runner/test/test_procmon.py:484:
DeprecationWarning: active is deprecated since Twisted 10.1.0.  Use running instead.
}}}','easy');
INSERT INTO "ticket" VALUES(4712,'enhancement',1288021341,1295222425,'core',NULL,'normal','','cyli','thijs',NULL,'','closed','fixed','Missing bits of statinfo accessors in FilePath','FilePath currently provides the following methods to get information in statinfo:

 * `getsize()`     (statinfo.st_size)
 * `getModificationTime()`    (statinfo.st_mtime)
 * `getStatusChangeTime()`     (statinfo.st_ctime)
 * `getAccessTime()`    (statinfo.st_atime)
 * `exists()`    (whether statinfo even exists)
 * `isdir()`    (part of st.st_mode)
 * `isfile()`    (part of st.st_mode)
 * `islink()`    (part of st.st_mode)

The following statinfo keys have no accessors  ([http://www.gnu.org/s/libc/manual/html_node/Attribute-Meanings.html meanings source]):

 * `st_ino` (The file serial number, which distinguishes this file from all other files on the same device)
 * `st_dev` (Identifies the device containing the file. The st_ino and st_dev, taken together, uniquely identify the file. The st_dev value is not necessarily consistent across reboots or system crashes, however.)
 * `st_nlink` (The number of hard links to the file. This count keeps track of how many directories have entries for this file. If the count is ever decremented to zero, then the file itself is discarded as soon as no process still holds it open. Symbolic links are not counted in the total.)
 * `st_uid` (The user ID of the file''s owner.)
 * `st_gid` (The group ID of the file)

If `FilePath.statinfo` is going to be deprecated, accessors to its keys should be provided.
Perhaps some of these (such as `st_ino` and `st_dev`) should not be exposed, but `twisted.protocols.ftp` for instance references `st_nlink`, `st_uid`, and `st_gid`; and `twisted.web2.static` references `st_ino`.

Note that this ticket is holding up #4711 and possibly #4450','easy');
CREATE TABLE ticket_change (ticket int not null, time int not null, author text, field text not null, oldvalue text, newvalue text, primary key (ticket, time, field));
INSERT INTO "ticket_change" VALUES(2723,1182815019,'glyph','description','The current, monolithic format is basically impossible for new users to approach and read, especially given that some of the humor is referencing really ancient stuff, and the first dozen or so quotes make ''''no'''' sense in the context of what Twisted is today.','= Problem =

The idea for a Twisted quotefile started with a tradition at Origin, where each released game included a quotefile from the game''s development team.  This allowed the users to get a feel for the developers'' culture, and the developers to feel a bit more connected to the users by sharing it.

At the time I originally thought of having a quote file, I assumed that the Twisted team would simply grow and the team would acquire new members over time; there was no "final release" so one quotefile that just got bigger made sense.

However, the current quotefile has several problems:

  * The default sort order when reading it in an editor or pager - newest quotes last - presents users first with the quotations least relevant to the current release of Twisted.
  * The quotefile is huge, and so readers are overwhelmed by its length and don''t read it as often as they used to.  (I am guessing this just from the amount of off-the-cuff feedback I used to get about the quotefile''s utility and the feedback I get now about its relative incomprehensibility.)
  * The quotefile includes lots of quotes from people who don''t even work on Twisted any more (and in many cases, never worked on Twisted).  Those quotes should''t be removed, since they were perhaps relevant to the hackers'' state of mind at the time, but again... not relevant today.

= Proposed Solution =

The quotefile for a given Twisted release should reflect the culture that produced that release.  The team around Twisted changes with the ebb and flow of different developers'' free time, so I think a good solution here would be to split the quotefile up into several different files, and only include one with each release.

If we ever manage to fix the problem that releases take a really long time, we might want to aggregate them differently, but I think for the time being one file / one release makes sense.');
INSERT INTO "ticket_change" VALUES(2723,1182815019,'glyph','summary','separate Twisted.Quotes into different quotefiles for each release','Twisted.Quotes does not serve its original intended purpose');
INSERT INTO "ticket_change" VALUES(2723,1182815019,'glyph','comment','1','exarkun complained -- and rightly so, I think -- that this ticket described a potential solution without really describing a problem.  I''ve completely replaced both the summary and the description to reflect what I really meant when I filed it.

Lots of tickets in Twisted (and other trackers, for that matter) suffer from this problem, and I hope that this ticket can serve as a useful example for how to better describe tickets in the future.');
INSERT INTO "ticket_change" VALUES(3312,1214493116,'exarkun','cc','','exarkun');
INSERT INTO "ticket_change" VALUES(3312,1214493116,'exarkun','milestone','Twisted-8.2','');
INSERT INTO "ticket_change" VALUES(3312,1214396675,'itamar','comment','1','1. If a log observer raises an exception, it gets removed (see http://twistedmatrix.com/trac/ticket/1069) - is it possible an exception is getting thrown there, causing logging to stop? One common cause is exceeding recursion limit.

2. Does this not happen with epoll? How about select()? Some Twisted reactors have issues when hitting their file descriptor limit, so maybe your kqueue settings limit you to 1024 fds.');
INSERT INTO "ticket_change" VALUES(3312,1214469914,'stupidInvaders','comment','2','1. We will try.
2. We didn''t check epoll. 

Select crash''s on Twisted 2.5.0 with many messages like this in stderr:

{{{
--- <exception caught here> ---
  File "/usr/local/lib/python2.4/site-packages/twisted/internet/posixbase.py", line 231, in mainLoop
    self.doIteration(t)
  File "/usr/local/lib/python2.4/site-packages/twisted/internet/selectreactor.py", line 97, in doSelect
    [], timeout)
  File "<string>", line 1, in fileno

  File "/usr/local/lib/python2.4/socket.py", line 136, in _dummy
    raise error(EBADF, ''Bad file descriptor'')
socket.error: (9, ''Bad file descriptor'')
Traceback (most recent call last):
  File "./MaffiaServerTwisted.py", line 116, in ?
    server.start()
  File "/usr/home/maffia/core/protocol.py", line 131, in start
    self.__reactor.run(installSignalHandlers=0)
  File "/usr/local/lib/python2.4/site-packages/twisted/internet/posixbase.py", line 220, in run
    self.mainLoop()
}}}

Server didn''t reach the limit of 1024 fds.
Ulimit sets to value that greatly exceed the required limit of fds.');
INSERT INTO "ticket_change" VALUES(3312,1214493116,'exarkun','comment','3','kqueuereactor in trunk isn''t well.  It doesn''t come close to passing the test suite.  See #1918 and #3114 for links to branches or diffs which change it, perhaps for the better.  If you''re interested in KQueue support, any help you can provide in getting these tickets resolved would be appreciated.

Since this isn''t a regression from a previous release (and officially, KQueue is not a "supported" event mechanism), I''m going to remove this ticket from the 8.2 milestone.  Our usage of release milestones is to indicate tickets which ''''''must'''''' be resolved for that release.  Generally, only regressions can block new releases.
');
INSERT INTO "ticket_change" VALUES(2723,1226268969,'thijs','status','new','assigned');
INSERT INTO "ticket_change" VALUES(2723,1226268969,'thijs','cc','','thijs');
INSERT INTO "ticket_change" VALUES(2723,1226268969,'thijs','launchpad_bug',NULL,'');
INSERT INTO "ticket_change" VALUES(2723,1226268969,'thijs','owner','glyph','thijs');
INSERT INTO "ticket_change" VALUES(2723,1226268969,'thijs','branch',NULL,'');
INSERT INTO "ticket_change" VALUES(2723,1226268969,'thijs','branch_author',NULL,'');
INSERT INTO "ticket_change" VALUES(2723,1226268969,'thijs','keywords','','fun');
INSERT INTO "ticket_change" VALUES(2723,1226268969,'thijs','comment','2','');
INSERT INTO "ticket_change" VALUES(2723,1237748799,'thijs','priority','low','lowest');
INSERT INTO "ticket_change" VALUES(2723,1237748799,'thijs','keywords','fun','fun, documentation');
INSERT INTO "ticket_change" VALUES(2723,1237748799,'thijs','status','assigned','new');
INSERT INTO "ticket_change" VALUES(2723,1237748799,'thijs','owner','thijs','glyph');
INSERT INTO "ticket_change" VALUES(2723,1237748799,'thijs','comment','3','Not sure where to start..');
INSERT INTO "ticket_change" VALUES(2723,1237754620,'glyph','owner','glyph','thijs');
INSERT INTO "ticket_change" VALUES(2723,1237754620,'glyph','comment','4','There are two possible parts to this solution.

The first, easy part, would be to move the current Twisted.Quotes to doc/historic/quotes/legacy.quotes, and add a step to the release process where we move Twisted.Quotes to doc/historic/quotes/<release>.quotes.

We''d keep putting new quotes into the root quotes file, and choose a QOTR out of that.

Of more historical interest would be to actually look at the timeline of commits to legacy.quotes and break it up into files for each release, i.e. doc/historic/quotes/1.0.quotes, 1.3.quotes, 2.0.quotes, etc.
');
INSERT INTO "ticket_change" VALUES(2723,1263586416,'thijs','cc','thijs','thijs, jesstess, khorn');
INSERT INTO "ticket_change" VALUES(2723,1263586416,'thijs','comment','5','');
INSERT INTO "ticket_change" VALUES(2723,1265243175,'thijs','comment','6','So there''s a news generator now with files in {{{topfiles}}} describing a change to twisted. I guess such a .quote file would go there as well, generated by something similar to that changelog tool?');
INSERT INTO "ticket_change" VALUES(2723,1267826635,'khorn','comment','7','thijs:

I actually came to this ticket just now intending to suggest exactly that.

You beat me to it.

+1');
INSERT INTO "ticket_change" VALUES(4712,1288021673,'cyli','description','FilePath currently provides the following methods to get information in statinfo:

* getsize()     (statinfo.st_size)
* getModificationTime()    (statinfo.st_mtime)
* getStatusChangeTime()     (statinfo.st_ctime)
* getAccessTime()    (statinfo.st_atime)
* exists()    (whether statinfo even exists)
* isdir()    (part of st.st_mode)
* isfile()    (part of st.st_mode)
* islink()    (part of st.st_mode)

The following statinfo keys have no accessors  ([http://www.gnu.org/s/libc/manual/html_node/Attribute-Meanings.html meanings source]):

* st_ino (The file serial number, which distinguishes this file from all other files on the same device)
* st_dev (Identifies the device containing the file. The st_ino and st_dev, taken together, uniquely identify the file. The st_dev value is not necessarily consistent across reboots or system crashes, however.)
* st_nlink (The number of hard links to the file. This count keeps track of how many directories have entries for this file. If the count is ever decremented to zero, then the file itself is discarded as soon as no process still holds it open. Symbolic links are not counted in the total.)
* st_uid (The user ID of the file''s owner.)
* st_gid (The group ID of the file)

If FilePath.statinfo is going to be deprecated, accessors to its keys should be provided.
Perhaps some of these (such as st_ino and st_dev) should not be exposed, but twisted.protocols.ftp for instance references st_nlink, st_uid, and st_gid.
','FilePath currently provides the following methods to get information in statinfo:

 * getsize()     (statinfo.st_size)
 * getModificationTime()    (statinfo.st_mtime)
 * getStatusChangeTime()     (statinfo.st_ctime)
 * getAccessTime()    (statinfo.st_atime)
 * exists()    (whether statinfo even exists)
 * isdir()    (part of st.st_mode)
 * isfile()    (part of st.st_mode)
 * islink()    (part of st.st_mode)

The following statinfo keys have no accessors  ([http://www.gnu.org/s/libc/manual/html_node/Attribute-Meanings.html meanings source]):

 * st_ino (The file serial number, which distinguishes this file from all other files on the same device)
 * st_dev (Identifies the device containing the file. The st_ino and st_dev, taken together, uniquely identify the file. The st_dev value is not necessarily consistent across reboots or system crashes, however.)
 * st_nlink (The number of hard links to the file. This count keeps track of how many directories have entries for this file. If the count is ever decremented to zero, then the file itself is discarded as soon as no process still holds it open. Symbolic links are not counted in the total.)
 * st_uid (The user ID of the file''s owner.)
 * st_gid (The group ID of the file)

If FilePath.statinfo is going to be deprecated, accessors to its keys should be provided.
Perhaps some of these (such as st_ino and st_dev) should not be exposed, but twisted.protocols.ftp for instance references st_nlink, st_uid, and st_gid; and twisted.web2.static references st_ino.
');
INSERT INTO "ticket_change" VALUES(4712,1288021673,'cyli','comment','1','');
INSERT INTO "ticket_change" VALUES(4712,1288021859,'cyli','branch','','branches/provide-statinfo-accessors-4712');
INSERT INTO "ticket_change" VALUES(4712,1288021859,'cyli','branch_author','','cyli');
INSERT INTO "ticket_change" VALUES(4712,1288021859,'cyli','comment','2','(In [30174]) Branching to ''provide-statinfo-accessors-4712''');
INSERT INTO "ticket_change" VALUES(4712,1288022172,'cyli','description','FilePath currently provides the following methods to get information in statinfo:

 * getsize()     (statinfo.st_size)
 * getModificationTime()    (statinfo.st_mtime)
 * getStatusChangeTime()     (statinfo.st_ctime)
 * getAccessTime()    (statinfo.st_atime)
 * exists()    (whether statinfo even exists)
 * isdir()    (part of st.st_mode)
 * isfile()    (part of st.st_mode)
 * islink()    (part of st.st_mode)

The following statinfo keys have no accessors  ([http://www.gnu.org/s/libc/manual/html_node/Attribute-Meanings.html meanings source]):

 * st_ino (The file serial number, which distinguishes this file from all other files on the same device)
 * st_dev (Identifies the device containing the file. The st_ino and st_dev, taken together, uniquely identify the file. The st_dev value is not necessarily consistent across reboots or system crashes, however.)
 * st_nlink (The number of hard links to the file. This count keeps track of how many directories have entries for this file. If the count is ever decremented to zero, then the file itself is discarded as soon as no process still holds it open. Symbolic links are not counted in the total.)
 * st_uid (The user ID of the file''s owner.)
 * st_gid (The group ID of the file)

If FilePath.statinfo is going to be deprecated, accessors to its keys should be provided.
Perhaps some of these (such as st_ino and st_dev) should not be exposed, but twisted.protocols.ftp for instance references st_nlink, st_uid, and st_gid; and twisted.web2.static references st_ino.
','FilePath currently provides the following methods to get information in statinfo:

 * getsize()     (statinfo.st_size)
 * getModificationTime()    (statinfo.st_mtime)
 * getStatusChangeTime()     (statinfo.st_ctime)
 * getAccessTime()    (statinfo.st_atime)
 * exists()    (whether statinfo even exists)
 * isdir()    (part of st.st_mode)
 * isfile()    (part of st.st_mode)
 * islink()    (part of st.st_mode)

The following statinfo keys have no accessors  ([http://www.gnu.org/s/libc/manual/html_node/Attribute-Meanings.html meanings source]):

 * st_ino (The file serial number, which distinguishes this file from all other files on the same device)
 * st_dev (Identifies the device containing the file. The st_ino and st_dev, taken together, uniquely identify the file. The st_dev value is not necessarily consistent across reboots or system crashes, however.)
 * st_nlink (The number of hard links to the file. This count keeps track of how many directories have entries for this file. If the count is ever decremented to zero, then the file itself is discarded as soon as no process still holds it open. Symbolic links are not counted in the total.)
 * st_uid (The user ID of the file''s owner.)
 * st_gid (The group ID of the file)

If FilePath.statinfo is going to be deprecated, accessors to its keys should be provided.
Perhaps some of these (such as st_ino and st_dev) should not be exposed, but twisted.protocols.ftp for instance references st_nlink, st_uid, and st_gid; and twisted.web2.static references st_ino.

Note that this ticket is holding up #4711 and possibly #4450');
INSERT INTO "ticket_change" VALUES(4712,1288022172,'cyli','comment','3','');
INSERT INTO "ticket_change" VALUES(4712,1293908163,'cyli','owner','glyph','');
INSERT INTO "ticket_change" VALUES(4712,1293908163,'cyli','comment','8','');
INSERT INTO "ticket_change" VALUES(4712,1293908140,'cyli','keywords','','review easy');
INSERT INTO "ticket_change" VALUES(4712,1293908140,'cyli','comment','7','Buildbot results:  http://buildbot.twistedmatrix.com/boxes-supported?branch=/branches/provide-statinfo-accessors-4712');
INSERT INTO "ticket_change" VALUES(4712,1293899615,'cyli','comment','4','(In [30408]) Added access methods to get FilePath.statinfo''s st_ino, st_dev, st_nlink, st_uid, and st_gid fields

refs #4712
');
INSERT INTO "ticket_change" VALUES(4712,1293906053,'cyli','comment','5','(In [30409]) Ensure that the device number is a long.

refs #4712
');
INSERT INTO "ticket_change" VALUES(4712,1293907263,'cyli','comment','6','(In [30410]) Ensure that the Inode Number is also a long.

refs #4712
');
INSERT INTO "ticket_change" VALUES(4712,1294012308,'thijs','cc','','thijs');
INSERT INTO "ticket_change" VALUES(4712,1294012308,'thijs','keywords','review easy','easy');
INSERT INTO "ticket_change" VALUES(4712,1294012308,'thijs','description','FilePath currently provides the following methods to get information in statinfo:

 * getsize()     (statinfo.st_size)
 * getModificationTime()    (statinfo.st_mtime)
 * getStatusChangeTime()     (statinfo.st_ctime)
 * getAccessTime()    (statinfo.st_atime)
 * exists()    (whether statinfo even exists)
 * isdir()    (part of st.st_mode)
 * isfile()    (part of st.st_mode)
 * islink()    (part of st.st_mode)

The following statinfo keys have no accessors  ([http://www.gnu.org/s/libc/manual/html_node/Attribute-Meanings.html meanings source]):

 * st_ino (The file serial number, which distinguishes this file from all other files on the same device)
 * st_dev (Identifies the device containing the file. The st_ino and st_dev, taken together, uniquely identify the file. The st_dev value is not necessarily consistent across reboots or system crashes, however.)
 * st_nlink (The number of hard links to the file. This count keeps track of how many directories have entries for this file. If the count is ever decremented to zero, then the file itself is discarded as soon as no process still holds it open. Symbolic links are not counted in the total.)
 * st_uid (The user ID of the file''s owner.)
 * st_gid (The group ID of the file)

If FilePath.statinfo is going to be deprecated, accessors to its keys should be provided.
Perhaps some of these (such as st_ino and st_dev) should not be exposed, but twisted.protocols.ftp for instance references st_nlink, st_uid, and st_gid; and twisted.web2.static references st_ino.

Note that this ticket is holding up #4711 and possibly #4450','FilePath currently provides the following methods to get information in statinfo:

 * `getsize()`     (statinfo.st_size)
 * `getModificationTime()`    (statinfo.st_mtime)
 * `getStatusChangeTime()`     (statinfo.st_ctime)
 * `getAccessTime()`    (statinfo.st_atime)
 * `exists()`    (whether statinfo even exists)
 * `isdir()`    (part of st.st_mode)
 * `isfile()`    (part of st.st_mode)
 * `islink()`    (part of st.st_mode)

The following statinfo keys have no accessors  ([http://www.gnu.org/s/libc/manual/html_node/Attribute-Meanings.html meanings source]):

 * `st_ino` (The file serial number, which distinguishes this file from all other files on the same device)
 * `st_dev` (Identifies the device containing the file. The st_ino and st_dev, taken together, uniquely identify the file. The st_dev value is not necessarily consistent across reboots or system crashes, however.)
 * `st_nlink` (The number of hard links to the file. This count keeps track of how many directories have entries for this file. If the count is ever decremented to zero, then the file itself is discarded as soon as no process still holds it open. Symbolic links are not counted in the total.)
 * `st_uid` (The user ID of the file''s owner.)
 * `st_gid` (The group ID of the file)

If `FilePath.statinfo` is going to be deprecated, accessors to its keys should be provided.
Perhaps some of these (such as `st_ino` and `st_dev`) should not be exposed, but `twisted.protocols.ftp` for instance references `st_nlink`, `st_uid`, and `st_gid`; and `twisted.web2.static` references `st_ino`.

Note that this ticket is holding up #4711 and possibly #4450');
INSERT INTO "ticket_change" VALUES(4712,1294012308,'thijs','owner','','cyli');
INSERT INTO "ticket_change" VALUES(4712,1294012308,'thijs','comment','9','All new methods need an `@since` marker.');
INSERT INTO "ticket_change" VALUES(4712,1294066896,'cyli','keywords','easy','easy review');
INSERT INTO "ticket_change" VALUES(4712,1294066896,'cyli','owner','cyli','');
INSERT INTO "ticket_change" VALUES(4712,1294066896,'cyli','comment','10','');
INSERT INTO "ticket_change" VALUES(4712,1294067096,'cyli','comment','11','(In [30411]) Added a @since to all the methods

refs #4712
');
INSERT INTO "ticket_change" VALUES(4712,1295216560,'cyli','owner','cyli','');
INSERT INTO "ticket_change" VALUES(4712,1295209969,'exarkun','keywords','easy review','easy');
INSERT INTO "ticket_change" VALUES(4712,1295209969,'exarkun','owner','','cyli');
INSERT INTO "ticket_change" VALUES(4712,1295209969,'exarkun','comment','12','Hooray

  1. in `test_statinfBitsAreNumbers`, any reason not to use `assertIsInstance`?  Not quite the same check, since it will allow subclasses, but is that really the concern?  Aside from that, `assertEquals` is preferred over `failUnlessEqual`.
  1. It might also be better, in `test_statinfBitsAreNumbers`, to populate the `FilePath` instance with a known `stat_result` object and make sure the right values come back from the right method calls.  `return 0` would appear to be a valid implementation at the moment.  This would also allow testing of the `restat` logic, which is currently uncovered (by returning the known `stat_result` from a monkey-patched `restat` method on the instance, for example).
  1. Copyright dates should be bumped to include 2011.
  1. The news file should go in `twisted/topfiles/` instead of `twisted/news/topfiles` :)

Thanks!');
INSERT INTO "ticket_change" VALUES(4712,1295213815,'cyli','comment','13','(In [30467]) Added a new test to monkey-patch restat, and ensure accessors are returning the correct values.

refs #4712
');
INSERT INTO "ticket_change" VALUES(4712,1295216560,'cyli','keywords','easy','easy review');
INSERT INTO "ticket_change" VALUES(4712,1295213857,'cyli','comment','12.14','>   1. in `test_statinfBitsAreNumbers`, any reason not to use `assertIsInstance`?  Not quite the same check, since it will allow subclasses, but is that really the concern?  Aside from that, `assertEquals` is preferred over `failUnlessEqual`.

Mainly laziness, so I don''t have to remember what is implemented as what (e.g. isinstance(True, int) is True).  But in this case, int and long are separate, so using assertIsInstance wouldn''t be a problem.  (Also realized I made a typo in the method name)  Changed.

>   1. It might also be better, in `test_statinfBitsAreNumbers`, to populate the `FilePath` instance with a known `stat_result` object and make sure the right values come back from the right method calls.  `return 0` would appear to be a valid implementation at the moment.  This would also allow testing of the `restat` logic, which is currently uncovered (by returning the known `stat_result` from a monkey-patched `restat` method on the instance, for example).

I put this part in a different test, since I was trying to ensure in the first test that the values returns were of the valid type.

>   1. Copyright dates should be bumped to include 2011.

Done

>   1. The news file should go in `twisted/topfiles/` instead of `twisted/news/topfiles` :)

Done');
INSERT INTO "ticket_change" VALUES(4712,1295216560,'cyli','comment','15','[http://buildbot.twistedmatrix.com/boxes-supported?branch=/branches/provide-statinfo-accessors-4712 build results]');
INSERT INTO "ticket_change" VALUES(4712,1295220639,'exarkun','keywords','easy review','easy');
INSERT INTO "ticket_change" VALUES(4712,1295220639,'exarkun','owner','','cyli');
INSERT INTO "ticket_change" VALUES(4712,1295220639,'exarkun','comment','16','There''s a stray print in `test_statinfoNumbersAreValid`.  Otherwise, looks great.  Please merge.');
INSERT INTO "ticket_change" VALUES(4712,1295221113,'cyli','comment','17','(In [30495]) Remove stray print

refs #4712
');
INSERT INTO "ticket_change" VALUES(4712,1295221329,'cyli','status','new','closed');
INSERT INTO "ticket_change" VALUES(4712,1295221329,'cyli','resolution',NULL,'fixed');
INSERT INTO "ticket_change" VALUES(4712,1295221329,'cyli','comment','18','(In [30497]) Merge provide-statinfo-accessors-4712: accessors to get the inode, device, hand hard link numbers, as well as uid and gid

Author: cyli
Reviewer: thijs, exarkun
Fixes: #4712

Provide accessors to get the inode number, device number, number of hard links, the user ID number, and group ID number of a FilePath file.
');
INSERT INTO "ticket_change" VALUES(4712,1295222230,'cyli','status','closed','reopened');
INSERT INTO "ticket_change" VALUES(4712,1295222230,'cyli','resolution','fixed','');
INSERT INTO "ticket_change" VALUES(4712,1295222230,'cyli','comment','19','(In [30500]) Reverse the merge because changing ''twisted'' to ''Twisted'' in Versions causes a failure in one of the new tests

reopens #4712
');
INSERT INTO "ticket_change" VALUES(4712,1295222425,'cyli','status','reopened','closed');
INSERT INTO "ticket_change" VALUES(4712,1295222425,'cyli','resolution','','fixed');
INSERT INTO "ticket_change" VALUES(4712,1295222425,'cyli','comment','20','(In [30501]) Merge provide-statinfo-accessors-4712: accessors to get the inode, device, hand hard link numbers, as well as uid and gid

Author: cyli Reviewer: thijs, exarkun Fixes: #4712

Provide accessors to get the inode number, device number, number of hard links, the user ID number, and group ID number of a FilePath file.  (Re-opened wrong ticket)
');
INSERT INTO "ticket_change" VALUES(4712,1297657849,'<automation>','owner','cyli','');
INSERT INTO "ticket_change" VALUES(2723,1297657849,'<automation>','owner','thijs','');
INSERT INTO "ticket_change" VALUES(3312,1327504599,'thijs','launchpad_bug',NULL,'');
INSERT INTO "ticket_change" VALUES(3312,1327504599,'thijs','comment','4','A new kqueue implementation was added in r33481 (#1918).');
INSERT INTO "ticket_change" VALUES(5517,1331152491,'thijs','description','`ProcessMonitor.active` in [source:trunk/twisted/runner/procmon.py] has been deprecated since 10.1 and can be removed.

{{{
twisted.runner.test.test_procmon.ProcmonTests.test_activeAttributeEqualsRunning ... [OK]
/home/buildbot/twisted/slave.trunk/fedora11-64bit-py2.7/Twisted/twisted/runner/test/test_procmon.py:484:
DeprecationWarning: active is deprecated since Twisted 10.1.0.  Use running instead.
}}}','`ProcessMonitor.active`, `consistencyDelay`, and `consistency` in [source:trunk/twisted/runner/procmon.py] are deprecated since 10.1 and can be removed.

{{{
twisted.runner.test.test_procmon.ProcmonTests.test_activeAttributeEqualsRunning ... [OK]
/home/buildbot/twisted/slave.trunk/fedora11-64bit-py2.7/Twisted/twisted/runner/test/test_procmon.py:484:
DeprecationWarning: active is deprecated since Twisted 10.1.0.  Use running instead.
}}}');
INSERT INTO "ticket_change" VALUES(5517,1331152491,'thijs','comment','1','');
INSERT INTO "ticket_change" VALUES(5517,1331531339,'candre717','owner','','candre717');
INSERT INTO "ticket_change" VALUES(5517,1331531339,'candre717','comment','2','');
INSERT INTO "ticket_change" VALUES(5517,1331532105,'candre717','keywords','easy','easy, review');
INSERT INTO "ticket_change" VALUES(5517,1331532105,'candre717','owner','candre717','');
INSERT INTO "ticket_change" VALUES(5517,1331532105,'candre717','comment','3','Attached is a patch for this issue, and I''ve confirmed that I ran a test suite and nothing broke from the changes. ');
INSERT INTO "ticket_change" VALUES(5517,1331535863,'habnabit','branch','','branches/remove-deprecated-5517');
INSERT INTO "ticket_change" VALUES(5517,1331535863,'habnabit','branch_author','','habnabit');
INSERT INTO "ticket_change" VALUES(5517,1331535863,'habnabit','comment','4','(In [33684]) Branching to ''remove-deprecated-5517''');
INSERT INTO "ticket_change" VALUES(5517,1331536152,'habnabit','comment','5','(In [33685]) Adding patch from ticket.

Refs #5517.

');
INSERT INTO "ticket_change" VALUES(5517,1331543886,'thijs','comment','6','The news file should go in `twisted/runner/topfiles`.');
INSERT INTO "ticket_change" VALUES(5517,1331575489,'habnabit','keywords','easy, review','easy');
INSERT INTO "ticket_change" VALUES(5517,1331575489,'habnabit','comment','7','Fix looks good; merging.');
INSERT INTO "ticket_change" VALUES(5517,1331576061,'habnabit','status','new','closed');
INSERT INTO "ticket_change" VALUES(5517,1331576061,'habnabit','resolution',NULL,'fixed');
INSERT INTO "ticket_change" VALUES(5517,1331576061,'habnabit','comment','8','(In [33690]) Merge remove-deprecated-5517: Remove deprecated t.r.procmon.ProcessMonitor.{active,consistencyDelay,consistency}.

Author: candre717
Reviewer: habnabit
Fixes: #5517

ProcessMonitor.active, consistencyDelay, and consistency in twisted.runner.procmon were deprecated since 10.1 have been removed.

');
INSERT INTO "ticket_change" VALUES(3312,1331618135,'MostAwesomeDude','status','new','closed');
INSERT INTO "ticket_change" VALUES(3312,1331618135,'MostAwesomeDude','resolution',NULL,'invalid');
INSERT INTO "ticket_change" VALUES(3312,1331618135,'MostAwesomeDude','comment','5','If this bug still applies to the modern, rewritten kqueue reactor, feel free to open a new bug, but this one is being closed.');
INSERT INTO "ticket_change" VALUES(3312,1332115134,'exarkun','status','reopened','closed');
INSERT INTO "ticket_change" VALUES(3312,1332115134,'exarkun','resolution','','fixed');
INSERT INTO "ticket_change" VALUES(3312,1332115134,'exarkun','comment','7','Using more recent versions of everything involved, and a tiny extra main script (not included in the ticket description, unfortunately), I can''t reproduce any problem with this code.  So, really fixed.  Thanks everybody.');
INSERT INTO "ticket_change" VALUES(3312,1332114515,'exarkun','status','closed','reopened');
INSERT INTO "ticket_change" VALUES(3312,1332114515,'exarkun','resolution','invalid','');
INSERT INTO "ticket_change" VALUES(3312,1332114515,'exarkun','comment','6','We generally shouldn''t close tickets like this.  The reporter gave us instructions for reproducing the issue.  We can try to reproduce it.  If it''s really gone, we can close the ticket as fixed.  If it''s still there, we know it''s a bug we should actually fix.

I''ll try to go reproduce the issue now and report back.');
INSERT INTO "ticket_change" VALUES(5622,1333844456,'exarkun','branch','','branches/tcp-endpoints-tests-refactor-5622');
INSERT INTO "ticket_change" VALUES(5622,1333844456,'exarkun','branch_author','','exarkun');
INSERT INTO "ticket_change" VALUES(5622,1333844456,'exarkun','comment','1','(In [34131]) Branching to ''tcp-endpoints-tests-refactor-5622''');
INSERT INTO "ticket_change" VALUES(5622,1333845773,'exarkun','keywords','tests','tests review');
INSERT INTO "ticket_change" VALUES(5622,1333845773,'exarkun','comment','2','Simple refactoring, no intended change in behavior, [http://buildbot.twistedmatrix.com/boxes-supported?branch=/branches/tcp-endpoints-tests-refactor-5622 build results] (hope they look good).');
INSERT INTO "ticket_change" VALUES(5622,1333849960,'itamar','comment','3','A quick glance suggests this a subset of the functionality in #5392 (which is still up for review). If that is correct, can we just get #5392 in instead?');
INSERT INTO "ticket_change" VALUES(2723,1334159815,'itamar','comment','9','A minimalist solution would be to reverse the sort order, so newer quotes are at the top.');
INSERT INTO "ticket_change" VALUES(2723,1334162096,'glyph','comment','12.13','Replying to [comment:12 itamar]:
> I still think we should reverse the chronological order on the quotes files. The current branch seems like only half a solution: irrelevant/confusing/embarrassingly juvenile quotes are still the first ones you read if you want to look at more than one quote.

I left the original quotefile as-is in order to allow a spelunker to more easily get ''svn blame'' to allow them to annotate quotes by actual date if they so desire, but I have no objection to adding new quotes at the top of the current file. ');
INSERT INTO "ticket_change" VALUES(2723,1334161367,'glyph','keywords','fun, documentation','fun, documentation, review');
INSERT INTO "ticket_change" VALUES(2723,1334161367,'glyph','comment','9.11','Replying to [comment:9 itamar]:
> A minimalist solution would be to reverse the sort order, so newer quotes are at the top.

Okay I implemented the "maximalist" solution instead, before this ticket turns into a kafka-esque parody of how our development process prevents anyone from ever getting anything done.  (Really?  "svn mv" is so much work that we have to start bikeshedding about alternative work-reducing approaches?)  I also added [http://twistedmatrix.com/trac/wiki/ReleaseProcess?action=diff&version=149 the relevant instruction to the release process here].');
INSERT INTO "ticket_change" VALUES(2723,1334161577,'itamar','comment','12','I still think we should reverse the chronological order on the quotes files. The current branch seems like only half a solution: irrelevant/confusing/embarrassingly juvenile quotes are still the first ones you read if you want to look at more than one quote.');
INSERT INTO "ticket_change" VALUES(5622,1334260992,'exarkun','keywords','tests review','tests');
INSERT INTO "ticket_change" VALUES(5622,1334260992,'exarkun','status','new','closed');
INSERT INTO "ticket_change" VALUES(5622,1334260992,'exarkun','resolution',NULL,'duplicate');
INSERT INTO "ticket_change" VALUES(5622,1334260992,'exarkun','comment','4','Superceded by #5392.');
INSERT INTO "ticket_change" VALUES(2723,1334160616,'glyph','branch','','branches/relevant-quotes-2723');
INSERT INTO "ticket_change" VALUES(2723,1334160616,'glyph','branch_author','','glyph');
INSERT INTO "ticket_change" VALUES(2723,1334160616,'glyph','comment','10','(In [34178]) Branching to ''relevant-quotes-2723''');
INSERT INTO "ticket_change" VALUES(2723,1334365493,'itamar','keywords','fun, documentation, review','fun, documentation');
INSERT INTO "ticket_change" VALUES(2723,1334365493,'itamar','owner','','itamar');
INSERT INTO "ticket_change" VALUES(2723,1334366119,'glyph','keywords','fun, documentation','fun, documentation, review');
INSERT INTO "ticket_change" VALUES(2723,1334366119,'glyph','owner','itamar','');
INSERT INTO "ticket_change" VALUES(2723,1334366119,'glyph','comment','14.15','Replying to [comment:14 itamar]:
> I don''t think this is good enough, so I guess I''ll do some more work myself.

Don''t think this is good enough for what?  Is it an improvement or not?  Does it address the problem or not?  If there''s more to do, please file separate tickets.  We don''t have to fix everything at once here.  This comment is not clear enough to constitute a review.');
INSERT INTO "ticket_change" VALUES(2723,1334365493,'itamar','comment','14','I don''t think this is good enough, so I guess I''ll do some more work myself.');
INSERT INTO "ticket_change" VALUES(2723,1334367409,'itamar','keywords','fun, documentation, review','fun, documentation');
INSERT INTO "ticket_change" VALUES(2723,1334367409,'itamar','owner','','glyph');
INSERT INTO "ticket_change" VALUES(2723,1334367409,'itamar','comment','16','Yeah, sorry about that. I''ll open separate ticket for splitting it up by year. Please merge.');
CREATE TABLE ticket_custom (ticket int not null, name text not null, value text, primary key (ticket, name));
INSERT INTO "ticket_custom" VALUES(3312,'branch_author','');
INSERT INTO "ticket_custom" VALUES(3312,'branch','');
INSERT INTO "ticket_custom" VALUES(2723,'launchpad_bug','');
INSERT INTO "ticket_custom" VALUES(2723,'branch','branches/relevant-quotes-2723');
INSERT INTO "ticket_custom" VALUES(2723,'branch_author','glyph');
INSERT INTO "ticket_custom" VALUES(4712,'branch','branches/provide-statinfo-accessors-4712');
INSERT INTO "ticket_custom" VALUES(4712,'branch_author','cyli');
INSERT INTO "ticket_custom" VALUES(4712,'launchpad_bug','');
INSERT INTO "ticket_custom" VALUES(3312,'launchpad_bug','');
INSERT INTO "ticket_custom" VALUES(5517,'branch','branches/remove-deprecated-5517');
INSERT INTO "ticket_custom" VALUES(5517,'branch_author','habnabit');
INSERT INTO "ticket_custom" VALUES(5517,'launchpad_bug','');
INSERT INTO "ticket_custom" VALUES(5622,'branch','branches/tcp-endpoints-tests-refactor-5622');
INSERT INTO "ticket_custom" VALUES(5622,'branch_author','exarkun');
INSERT INTO "ticket_custom" VALUES(5622,'launchpad_bug','');
CREATE TABLE attachment (type text not null, id text not null, filename text not null, size int, time int, description text, author text, ipnr text, primary key (type, id, filename));
INSERT INTO "attachment" VALUES('ticket','5517','5517.diff',3472,1331531954,'','candre717','66.35.39.65');
create table auth_cookie (cookie text, name text, ipnr text, time int);
insert into "auth_cookie" values('a331422278bd676f3809e7a9d8600647','alice','',1336068159);
create table session (sid text, authenticated bool, last_visit int);
insert into "session" values ('alice',1,1336068158);
create table session_attribute (sid text, authenticated bool, name text, value text);
insert into "session_attribute" values('alice',1,'email','alice@example.com');
COMMIT;
