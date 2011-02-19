import socket, sys, time, subprocess, threading, signal
import TorCtl.TorCtl

debug = sys.stderr
HOST = '127.0.0.1'
PORT = 10951

shared = dict(
  torprocess = None,
  torlock = threading.Lock()
)

TORRC = """\
SocksListenAddress %s
SocksPort %d
ControlPort %d
CookieAuthentication 1
RunAsDaemon 0
Log info file logfile
DataDir .tor
""" % (HOST, PORT, PORT+1)

def start_tor():
    global TORPROCESS
    file('torrc', 'w').write(TORRC)
    shared['torprocess'] = subprocess.Popen(['tor', '-f', 'torrc'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    shared['torlock'].acquire()

def end_tor(signum=None, frame=None):
    shared['torprocess'].kill()
signal.signal(signal.SIGTERM, end_tor)

triggers = dict(
    GOT_TOR = 'Bootstrapped 100%: Done.',
    GOT_REQUEST = 'Got a hidden service request for ID',
    START_FETCH = 'Sending fetch request for v2 descriptor',
    END_FETCH = 'Successfully fetched v2 rendezvous descriptor.',
    START_RENDCIRC = 'Sending an ESTABLISH_RENDEZVOUS cell',
    GOT_RENDCIRC = 'Got rendezvous ack. This circuit is now ready for rendezvous.',
    GOT_INTROCIRC = 'introcirc is open',
    # SEND_INTRODUCE1
    GOT_RENDEZVOUS2 = 'Got RENDEZVOUS2 cell from hidden service'
)

class EventHandler(TorCtl.TorCtl.DebugEventHandler):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.last_event = None
        TorCtl.TorCtl.DebugEventHandler.__init__(self)
    
    def declare(self, declaration):
        print declaration
    
    def log(self, event):
        now = time.time()
        print now, event,
        if self.last_event:
            print '(%.2f seconds)' % (now-self.last_event)
        else:
            print
        self.last_event = now
    
    def msg_event(self, log_event):
        for k in triggers:
            if triggers[k] in log_event.msg:
                self.log(k)
                if k == 'GOT_TOR': shared['torlock'].release()
                break

def grab_page(h, u):
    h.last_event = None
    h.declare('GET %s' % u)
    h.log('START_REQUEST')
    p = subprocess.Popen(['curl', '-sN', '--socks4a', h.host + ':%d' % (h.port-1),
     u], bufsize=0, stdout=subprocess.PIPE)
    b = ''
    while not b: b = p.stdout.read(1)
    h.log('GOT_FIRST_BYTE')
    while b: b = p.stdout.read()
    h.log('GOT_LAST_BYTE')
    h.log('END_REQUEST')

def main(host, port):
    handler = EventHandler(host, port+1)
    handler.log('START_TOR')
    start_tor()
    time.sleep(2)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port+1))
    c = TorCtl.TorCtl.Connection(s)
    c.set_event_handler(handler)
    c.authenticate()
    EVT = TorCtl.TorCtl.EVENT_TYPE
    c.set_events([EVT.INFO, EVT.NOTICE])
    shared['torlock'].acquire()

    grab_page(handler, 'http://pevf7ega6sg6elzr.onion:9081/50kbfile')
    grab_page(handler, 'http://torperf.tor2web.org:9081/50kbfile')
    time.sleep(10)
    grab_page(handler, 'http://pevf7ega6sg6elzr.onion:9081/50kbfile')
    grab_page(handler, 'http://torperf.tor2web.org:9081/50kbfile')
    time.sleep(10)
    grab_page(handler, 'http://pevf7ega6sg6elzr.onion:9081/50kbfile')
    grab_page(handler, 'http://torperf.tor2web.org:9081/50kbfile')
    handler.log('END_TOR')

if __name__ == "__main__":
    try:
        main(HOST, PORT)
    except KeyboardInterrupt:
        end_tor()
    finally:
        end_tor()