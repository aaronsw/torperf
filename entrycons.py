#!/usr/bin/python
import sys, time
import TorCtl.TorCtl as TorCtl
import TorCtl.TorUtil as TorUtil
import copy

HOST = "127.0.0.1"

SAMPLE_SIZE = 3

class EntryTracker(TorCtl.ConsensusTracker):
  used_entries = []

  def __init__(self, conn, speed):
    TorCtl.ConsensusTracker.__init__(self, conn, consensus_only=False)
    self.speed = speed
    self.set_entries()

  def new_consensus_event(self, n):
    TorCtl.ConsensusTracker.new_consensus_event(self, n)
    TorUtil.plog("INFO", "New consensus arrived. Rejoice!")
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
        TorUtil.plog("NOTICE", "Entry: " + event.nick + ":" + event.idhex +
                     " died, and we replaced it with: " + nodes_list[-1] + "!")
        nodes_tuple = self.c.get_option("EntryNodes")
        nodes_list = nodes_tuple[0][1]
        TorUtil.plog("INFO", "New nodes_list: " + nodes_list)
      except ValueError:
        TorUtil.plog("INFO", "GUARD event notified of an entry death that " +
                     "is not in nodes_list! Mysterioush!")
        TorUtil.plog("INFO", "It was: " + event.nick + " : " + event.idhex)

  def sort_routers(self, sorted_routers):
    routers = copy.copy(sorted_routers)
    def ratio_cmp(r1, r2):
      if r1.bw/float(r1.desc_bw) > r2.bw/float(r2.desc_bw):
        return -1
      elif r1.bw/float(r1.desc_bw) < r2.bw/float(r2.desc_bw):
        return 1
      else:
        return 0

    if self.speed == "fast":
      pass # no action needed
    elif self.speed == "slow":
      routers.reverse()
    elif self.speed == "fastratio":
      routers.sort(ratio_cmp)
    elif self.speed == "slowratio":
      routers.sort(lambda x,y: ratio_cmp(y,x))

    # Print top 5 routers + ratios
    for i in xrange(5):
      TorUtil.plog("DEBUG", self.speed+" router "+routers[i].nickname+" #"+str(i)+": "
                    +str(routers[i].bw)+"/"+str(routers[i].desc_bw)+" = "
                    +str(routers[i].bw/float(routers[i].desc_bw)))

    return routers

  def get_next_router(self, event, nodes_list):
    # XXX: This is inefficient, but if we do it now, we're sure that
    # we're always using the very latest networkstatus and descriptor data
    sorted_routers = self.sort_routers(self.current_consensus().sorted_r)

    i = 0
    while (1):
      if ((sorted_routers[i].idhex not in self.used_entries) and
          (not sorted_routers[i].down
           and "Guard" in sorted_routers[i].flags)):
        self.used_entries.append(sorted_routers[i].idhex)
        return sorted_routers[i].idhex
      i += 1

  def set_entries(self):
    # XXX: This is inefficient, but if we do it now, we're sure that
    # we're always using the very latest networkstatus and descriptor data
    sorted_routers = self.sort_routers(self.current_consensus().sorted_r)

    entry_nodes = []
    for i in xrange(len(sorted_routers)):
      if len(entry_nodes) >= SAMPLE_SIZE: break
      if (not sorted_routers[i].down and "Guard" in sorted_routers[i].flags):
        entry_nodes.append(sorted_routers[i].idhex)
        self.used_entries.append(sorted_routers[i].idhex)
    self.c.set_option("EntryNodes", ",".join(entry_nodes))
    TorUtil.plog("NOTICE", self.speed+": Changed EntryNodes to: " +
                   ",".join(map(lambda x: self.ns_map[x].nickname+"="+x,
                                entry_nodes)))

def usage():
  print "Usage: "+sys.argv[0]+" <Tor control port> <fast|slow|fastratio|slowratio>"

def main():
  if len(sys.argv) < 3:
    usage()
    return

  port = int(sys.argv[1])
  speed = sys.argv[2]

  if not speed in ("fast", "slow", "fastratio", "slowratio"):
    TorUtil.plog("ERROR",
        "Second parameter must be 'fast', 'slow', 'fastratio', or 'slowratio'")
    return

  conn = TorCtl.connect(HOST, port)

  conn.set_events(["NEWCONSENSUS", "NEWDESC", "NS", "GUARD"])
  conn.set_option("StrictEntryNodes", "1")
  conn.set_option("UseEntryNodes", "1")

  EntryTracker(conn, speed)
  conn.block_until_close()

if __name__ == '__main__':
  main()
