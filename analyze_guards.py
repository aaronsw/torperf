#!/usr/bin/python
#
# This script takes a list of $idhex=nickname OR nickname=idhex lines and
# prints out min, avg, dev, max statistics based on the current consensus.
#
# Be sure to include ratio in the filenames of idhexes that are supposedly
# chosen by consensus to descriptor ratio values.
#
# Here is an example scriptlet for extracting the guards from an extrainfo
# file:
#   awk '{ print $3; }' < torperfslowratio-50kb.extradata > slowratio50kb.extra
#
# Use this result like this:
# ./analyze_guards.py slowratio50kb.extra
#
# It should then print out ranking stats. Use your brain to determine if these
# stats make sense for the run you selected.

import sys
import math

import TorCtl.TorCtl
import TorCtl.TorUtil

TorCtl.TorUtil.loglevel = "NOTICE"
HOST="127.0.0.1"
PORT=9051

def analyze_list(router_map, idhex_list):
  min_rank = len(router_map)
  tot_rank = 0
  max_rank = 0
  absent = 0
  for idhex in idhex_list:
    if idhex not in router_map:
      absent += 1
      continue

    rank = router_map[idhex].list_rank
    tot_rank += rank
    if rank < min_rank: min_rank = rank
    if rank > max_rank: max_rank = rank

  avg = float(tot_rank)/(len(idhex_list)-absent)
  varience = 0

  for idhex in idhex_list:
    if idhex not in router_map: continue
    rank = router_map[idhex].list_rank
    varience += (rank-avg)*(rank-avg)

  return (min_rank, avg, math.sqrt(varience/(len(idhex_list)-absent-1)), max_rank, absent)

def main():
  f = file(sys.argv[1], "r")
  idhex_list = f.readlines()

  for i in xrange(len(idhex_list)):
    if "~" in idhex_list[i]: char = "~"
    else: char = "="

    split = idhex_list[i].split(char)

    if split[0][0] == "$":
      idhex_list[i] = split[0]
    else:
      idhex_list[i] = "$"+split[1]

  c = TorCtl.TorCtl.connect(HOST, PORT)
  nslist = c.get_network_status()
  sorted_rlist = filter(lambda r: r.desc_bw > 0, c.read_routers(c.get_network_status()))
  router_map = {}
  for r in sorted_rlist: router_map["$"+r.idhex] = r

  if "ratio" in sys.argv[1]:
    print "Using ratio rankings"
    def ratio_cmp(r1, r2):
      if r1.bw/float(r1.desc_bw) > r2.bw/float(r2.desc_bw):
        return -1
      elif r1.bw/float(r1.desc_bw) < r2.bw/float(r2.desc_bw):
        return 1
      else:
        return 0
    sorted_rlist.sort(ratio_cmp)
  else:
    print "Using consensus bw rankings"
    sorted_rlist.sort(lambda x, y: cmp(y.bw, x.bw))

  for i in xrange(len(sorted_rlist)): sorted_rlist[i].list_rank = i

  print "Guard rank stats (min, avg, dev, total, absent): "
  print str(analyze_list(router_map, idhex_list))

if __name__ == '__main__':
  main()

