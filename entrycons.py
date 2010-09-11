#!/usr/bin/python
import sys, time
import TorCtl.TorCtl as TorCtl
import TorCtl.TorUtil as TorUtil

HOST = "127.0.0.1"

SAMPLE_SIZE = 3

class EntryTracker(TorCtl.ConsensusTracker):
  used_entries = []

  def __init__(self, conn, slow):
    TorCtl.ConsensusTracker.__init__(self, conn, consensus_only=False)
    self._slow = slow
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

  def get_next_router(self, event, nodes_list):
    cons = self.current_consensus()
    sorted_routers = cons.sorted_r

    i = 0
    while (1):
      if ((sorted_routers[i].idhex not in self.used_entries) and
          (not sorted_routers[i].down
           and "Guard" in sorted_routers[i].flags)):
        self.used_entries.append(sorted_routers[i].idhex)
        return sorted_routers[i].idhex
      i += 1

  def set_entries(self):
    sorted_routers = self.sorted_r

    if (not self._slow):
      fast_entry_nodes = []
      for i in xrange(len(sorted_routers)):
        if len(fast_entry_nodes) >= SAMPLE_SIZE: break
        if (not sorted_routers[i].down and "Guard" in sorted_routers[i].flags):
          fast_entry_nodes.append(sorted_routers[i].idhex)
          self.used_entries.append(sorted_routers[i].idhex)
      self.c.set_option("EntryNodes", ",".join(fast_entry_nodes))
    else:
      sorted_routers.reverse()
      slow_entry_nodes = []
      for i in xrange(len(sorted_routers)):
        if len(slow_entry_nodes) >= SAMPLE_SIZE: break
        if (not sorted_routers[i].down and "Guard" in sorted_routers[i].flags):
          slow_entry_nodes.append(sorted_routers[i].idhex)
          self.used_entries.append(sorted_routers[i].idhex)
      self.c.set_option("EntryNodes", ",".join(slow_entry_nodes))

    if (not self._slow):
      TorUtil.plog("NOTICE", "Changed EntryNodes to: " +
                   ",".join(map(lambda x: self.ns_map[x].nickname+"="+x,
                                fast_entry_nodes)))
    else:
      TorUtil.plog("NOTICE", "SLOW: Changed EntryNodes to: " +
                   ",".join(map(lambda x: self.ns_map[x].nickname+"="+x,
                                slow_entry_nodes)))

def main():

  port = int(sys.argv[1])
  speed = sys.argv[2]
  
  if not speed in ("fast", "slow"):
    TorUtil.plot("ERROR", "Second parameter must be 'fast' or 'slow'");

  conn = TorCtl.connect(HOST, port)

  conn.set_events(["NEWCONSENSUS", "NEWDESC", "NS", "GUARD"])
  conn.set_option("StrictEntryNodes", "1")

  EntryTracker(conn, speed == "slow")
  conn.block_until_close()

if __name__ == '__main__':
  main()
