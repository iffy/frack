# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
import pprint, sys, textwrap, time, datetime
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.internet.endpoints import clientFromString
from twisted.protocols import amp
from twisted.python import usage, log
from frack.responder import FetchTicket

def termsize():
    import fcntl, termios, struct
    return struct.unpack('hh', fcntl.ioctl(1, termios.TIOCGWINSZ,
                                           '1234'))



class Options(usage.Options):
    synopsis = "frack.ampclient [options] <ticket id>"

    optParameters = [['port', 'p', 'tcp:host=localhost:port=1352',
                      'Service description for the AMP connector.']]

    def parseArgs(self, id):
        self['id'] = int(id)



class AMPClientFffffff(ClientFactory):
    noisy = False
    def __init__(self, cb):
        self.cb = cb

    def buildProtocol(self, addr):
        self.p = amp.AMP()
        self.p.factory = self
        reactor.callLater(0, self.cb, self.p)
        return self.p



def convertTime(unixtime):
    return datetime.datetime(*time.gmtime(unixtime)[:6])



def wrapParagraphs(content, width, indentLevel):
    indent = " " * indentLevel
    paras = content.split('\r\n\r\n')
    out = []
    for para in paras:
        yield textwrap.fill(
                    para, width=width - 8,
                    replace_whitespace=False, initial_indent=indent,
                    subsequent_indent=indent) + '\n'



def format(response):
    height, width = termsize()
    response['time'] = convertTime(response['time'])
    headline = "* #%(id)s - %(owner)s - %(summary)s [%(status)s] - " % response
    subline = ("`-- keywords: %(keywords)s reporter: %(reporter)s "
               "component: %(component)s" % response)
    indent = " " * 4
    body = textwrap.wrap(response['description'], width=width - 8,
                         replace_whitespace=False,
                         initial_indent=indent, subsequent_indent=indent)

    changes = ['\n']
    for item in response['changes']:
        item['time'] = convertTime(item['time'])
        if item['field'] == 'comment':
            changes.append('    ** %(author)s - %(time)s #%(oldvalue)s' % item)
            comment = wrapParagraphs(item['newvalue'], width, 8)
            changes.extend(comment)
            changes.append('\n')
        else:
            changes.append('# %(author)s changed %(field)s: '
                           '%(oldvalue)s -> %(newvalue)s' % item)
    sys.__stdout__.write('\n'.join([headline, subline] + body + changes +
                                   ['\n']))



def die(e):
    log.err(e)
    reactor.stop()



def main(config):
    def fetch(p):
        d = p.callRemote(FetchTicket, id=config['id'], asHTML=False)
        d.addCallback(format)
        d.addCallback(lambda _: reactor.stop())
        d.addErrback(die)
    
    clientFromString(reactor, config['port']).connect(AMPClientFffffff(fetch))
    log.startLogging(sys.stdout)
    reactor.run()



if __name__ == '__main__':
    o = Options()
    o.parseOptions()
    main(o)


