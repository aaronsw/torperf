import socket,sys,re,os,getopt
sys.path.append("/home/broo/tor/torctl/trunk/python/TorCtl")
import TorCtl

HOST = "127.0.0.1"
PORT = 9060
AUTH = "broom"

SAMPLE_SIZE = 3

slow = False

class EntryTracker(TorCtl.ConsensusTracker):
  global slow
  used_entries = []

  def __init__(self, c):
    TorCtl.ConsensusTracker.__init__(self, c)
    self.set_entries()

  def new_consensus_event(self, n):
    TorCtl.ConsensusTracker.new_consensus_event(self, n)
    print "DEBUG: New consensus arrived. Rejoice!"
    self.used_entries = []
    self.set_entries()

  def guard_event(self, event):
    TorCtl.EventHandler.guard_event(self, event)
    self.handle_entry_deaths(event)

  def handle_entry_deaths(self, event):
    state = event.status
    if (state == "DOWN" or state == "BAD" or state == "DROPPED"):
      nodes_tuple = self.c.get_option("EntryNodes")
      nodes_list = nodes_tuple[0][1].split(",")
      try: 
        nodes_list.remove(event.idhex)
        nodes_list.append(self.get_next_router(event.idhex, nodes_list))
        self.c.set_option("EntryNodes", ",".join(nodes_list))
        print "DEBUG: Entry: " + event.nick + ":" + event.idhex + " died, and we replaced it with: " + nodes_list[2] + "!"
        nodes_tuple = self.c.get_option("EntryNodes")
        nodes_list = nodes_tuple[0][1]
        print "DEBUG: New nodes_list: " + nodes_list
      except ValueError:
        print "DEBUG: GUARD event notified of an entry death that is not in nodes_list! Mysterioush!"
        print "DEBUG: It was: " + event.nick + " : " + event.idhex

  def get_next_router(self, event, nodes_list):
    cons = self.current_consensus()
    sorted_routers = cons.sorted_r

    i = 0
    while (1):
      if ((sorted_routers[i].idhex not in self.used_entries) and (not sorted_routers[i].down)):
        self.used_entries.append(sorted_routers[i].idhex)
        return sorted_routers[i].idhex
      i += 1

  def set_entries(self):
    sorted_routers = self.sorted_r

    if (not slow):
      fast_entry_nodes = []
      for i in range(SAMPLE_SIZE):
        if (not sorted_routers[i].down):
          fast_entry_nodes.append(sorted_routers[i].idhex)
          self.used_entries.append(sorted_routers[i].idhex)
      self.c.set_option("EntryNodes", ",".join(fast_entry_nodes))
    else:
      sorted_routers.reverse()
      i=0
      for k in sorted_routers:
        print sorted_routers[i].nickname + " : " + sorted_routers[i].idhex
        i += 1
      slow_entry_nodes = []
      for i in range(SAMPLE_SIZE):
        if (not sorted_routers[i].down):
          slow_entry_nodes.append(sorted_routers[i].idhex)
          self.used_entries.append(sorted_routers[i].idhex)
      self.c.set_option("EntryNodes", ",".join(slow_entry_nodes))

    if (not slow):
      print "DEBUG: Changed EntryNodes to: " + ",".join(fast_entry_nodes)
    else:
      print "DEBUG: SLOW: Changed EntryNodes to: " + ",".join(slow_entry_nodes)

def usage():
  print sys.argv[0] + " [options]"
  print "Options:\n\t -h/--help: Print this cute message."
  print "\t -s/--slow: Choose slowest guards."

def main(argv):

  global slow
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((HOST, PORT))
  c = TorCtl.Connection(s)
  th = c.launch_thread()
  c.authenticate(AUTH)

  c.set_events(["NEWCONSENSUS", "GUARD"])
  c.set_option("StrictEntryNodes", "1")

  try:
    opts,args = getopt.getopt(argv, "hs", ["help", "slow"])
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  for opt, arg in opts:
    if opt in ("-h","--help"):
      usage()
      sys.exit()
    elif opt in ("-s","--slow"):
      print ".Shlow."
      slow = True

  EntryTracker(c)
  th.join()

if __name__ == '__main__':
  main(sys.argv[1:])
