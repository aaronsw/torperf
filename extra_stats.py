import sys, time, math
import TorCtl.TorCtl as TorCtl

HOST = "127.0.0.1"

class WriteStats(TorCtl.PostEventListener):
  def __init__(self, port, filename):
    TorCtl.PostEventListener.__init__(self)
    self._port = int(port)
    self._filename = filename
    self._conn = None

  def connect(self):
    self._conn = TorCtl.connect(HOST, self._port)
    if not self._conn
      sys.exit(2)

  def setup_listener(self):
    self._conn.set_events(["Stream"])
    self._conn.add_event_listener(self)

  def stream_status_event(self, event):
    if event.source == 'EXIT' or \
       event.status == 'DETACHED':
      for circs in self._conn.get_info( "circuit-status").itervalues():
        for circ in circs.split("\n"):
          entry = circ.split(" ")
          if entry[0] == str(event.circ_id):
            if event.source == 'EXIT':
              self.write_result(True, event.arrived_at, entry[2].split(","))
            else:
              self.write_result(False, event.arrived_at, entry[2].split(","))

  def write_result(self, successful, now, relays):
    success = ""
    if successful:
      success = "ok"
    else:
      success = "error"

    statsfile = open(self._filename, 'a')
    statsfile.write("%s %d %s\n" % (success, math.floor(now), " ".join(relays)))
    statsfile.close()

def main():
  if len(sys.argv) < 3:
    print "Bad arguments"
    sys.exit(1)

  port = sys.argv[1]
  filename = sys.argv[2]

  stats = WriteStats(port, filename)
  stats.connect()
  stats.setup_listener()
  try:
    while True:
      time.sleep(500)
  except:
    pass

if __name__ == '__main__':
  main()

