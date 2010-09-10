#!/usr/bin/python

### Copyright 2007 Steven J. Murdoch
### See LICENSE for licensing information

import os
import time

## Configuration

## Files to download
bigfile1 = ## location of big file on server 1
smallfiler2 = ## location of a small file on server 2
bigfile2 = ## location of a big file on server 2

## Duration of a experiment
test_duration = 15 * 60 ## Should be > 10min to ensure circuits are not re-used

## Duration of a sub-experiment
delay = test_duration/2

## Main program

def write_header(filename):
    ## Write file header
    fh = file(filename, "wt")
    fh.write("startsec startusec \
    socketsec socketusec \
    connectsec connectusec \
    negotiatesec negotiateusec \
    requestsec requestusec \
    responsesec responseusec \
    datarequestsec, datarequestusec \
    dataresponsesec, dataresponseusec \
    datacompletesec, datacompleteusec \
    writebytes readbytes\n")
    fh.close()

write_header("first-small.data")
write_header("first-big.data")
write_header("second-big.data")

wait = 0
for i in range(104):
    if wait > 0:
        time.sleep(wait)

    one_file = (i % 2) == 0
    if one_file:
        test_type = "one file"
    else:
        test_type = "two files"

    print "Starting run (%s)"%test_type, i, "at", time.asctime()
    
    start = time.time()
    if one_file:
        os.system("./trivsocks-client %s %s >> first-big.data 2>/dev/null"%bigfile1)
    else:
        os.system("./trivsocks-client %s %s >> first-small.data 2>/dev/null"%smallfile2)
        os.system("./trivsocks-client %s %s >> second-big.data 2>/dev/null"%bigfile2)
        
    wait = start + delay - time.time()
    print "Finished run (%s)"%test_type, i, "at", time.asctime(), "waiting for %5f s"%wait
