# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
import pprint, sys, textwrap, time, datetime
import simplejson as json
from itertools import count
from twisted.internet import reactor
from twisted.web.client import getPage
from twisted.protocols import amp
from twisted.python import usage, log

def termsize():
    import fcntl, termios, struct
    try:
        return struct.unpack('hh', fcntl.ioctl(1, termios.TIOCGWINSZ,
                                               '1234'))
    except IOError:
        return 24, 80



class Options(usage.Options):
    synopsis = "frack.ampclient [options] <ticket id>"

    optParameters = [['uri', 'u', 'http://localhost:1353/amp', 'JSON-RPC URI.']]

    def parseArgs(self, id):
        self['id'] = int(id)



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
    subline = ("`-- keywords: %(keywords)s reporter: %(reporter)s"
               " component: %(component)s" % response)
    indent = " " * 4
    body = textwrap.wrap(response['description'], width=width - 8,
                         replace_whitespace=False, initial_indent=indent,
                         subsequent_indent=indent)

    changes = ['\n']
    for item in response['changes']:
        item['time'] = convertTime(item['time'])
        if item['field'] == 'comment':
            changes.append('    ** %(author)s - %(time)s #%(oldvalue)s' % item)
            comment = wrapParagraphs(item['newvalue'], width, 8)
            changes.extend(comment)
            changes.append('\n')
        else:
            changes.append('# %(author)s changed %(field)s: %(oldvalue)s '
                           '-> %(newvalue)s' % item)
    sys.__stdout__.write('\n'.join([headline, subline] + body + changes +
                                   ['\n']))



def die(e):
    log.err(e)
    reactor.stop()



cc = count()

def fetchTicket(id):
    return json.dumps({'jsonrpc': '2.0',
                       'method': 'FetchTicket',
                       'params': {'id': id, 'asHTML': False},
                       'id': cc.next()})



def decode(response):
    r = json.loads(response)
    if r.get('error'):
        print 'omg', r['error']
        reactor.stop()
        raise RuntimeError(r['error'])
    else:
        return r['result']



def main(config):
    msg = fetchTicket(config['id'])
    d = getPage(config['uri'], method='POST', postdata=msg)
    d.addCallback(decode)
    d.addCallback(format)
    d.addCallback(lambda _: reactor.stop())
    d.addErrback(die)

    log.startLogging(sys.stdout)
    reactor.run()



if __name__ == '__main__':
    o = Options()
    o.parseOptions()
    main(o)


