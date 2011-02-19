def get_count(line):
    return float(line.split()[0])

counts = dict(
  torboot = [],
  grab = {},
)

mode = None
for line in file('torperf2.log'):
    if 'START_TOR' in line:
        mode = 'torboot'
        start = get_count(line)
    
    elif 'GOT_TOR' in line and mode == 'torboot':
        counts['torboot'].append(get_count(line)-start)
        mode = None
    
    elif line.startswith('GET'):
        mode = 'grab'
        try:
            bucket = line.split()[2]
        except IndexError:
            mode = None
            continue
        
    elif 'START_REQUEST' in line and mode == 'grab':
        start = get_count(line)
    
    elif 'END_REQUEST' in line and mode == 'grab':
        counts['grab'].setdefault(bucket, []).append(
          get_count(line)-start
        )

def avg(dist):
    return sum(dist)/float(len(dist))

def median(dist):
    return sorted(dist)[len(dist)//2]

def stddev(dist):
    sdsq = sum((i - avg(dist)) ** 2 for i in dist)
    return (sdsq / (len(dist) - 1)) ** .5

def distfacts(dist):
    if len(dist) <= 1: return repr(dist)
    return '%.2f, %.2f, %.2f' % (avg(dist), median(dist), stddev(dist))

print "thing: avg, median, mode"
print 'torboot:', distfacts(counts['torboot'])
for k in counts['grab']:
    print '%s: %s' % (k, distfacts(counts['grab'][k]))
