###
#   Call this with 4 parameters: the file to read data from, the file to read
#   extradata from, the file to write the combined data to, the slack interval
#   to match data and extradata timestamps.
#
#   IMPORTANT: You need to manually sort -g the data file, because torperf
#   might screw up ordering and this script expects sorted lines!
###

import sys, time

class Data:
  def __init__(self, filename, mode="r"):
    self._filename = filename
    self._file = open(filename, mode)

  def prepline(self):
    line = self._file.readline()
    if line == "" or line == "\n":
      raise StopIteration
    if line[-1] == "\n":
      line = line[:-1]
    return line.split(" ")

  def next(self):
    return self.prepline()

  def __iter__(self):
    return self

class ExtraData(Data):
  def __init__(self, filename):
    Data.__init__(self, filename)
    self._curData = None
    self._retCurrent = False

  def next(self):
    if self._retCurrent == True:
      self._retCurrent = False
      return self._curData
    cont = self.prepline()
    if cont[0] == "ok":
      self._curData = cont[1:]
      return self._curData
    print('Ignoring line "' + " ".join(cont) + '"')
    return self.next()

  def keepCurrent(self):
    self._retCurrent = True

class NormalData(Data):
  def __init__(self, filename):
    Data.__init__(self, filename)

class BetterData(Data):
  def __init__(self, filename):
    Data.__init__(self, filename, "w")

  def writeLine(self, line):
    self._file.write(" ".join(line) + "\n")

def main():
  if len(sys.argv) < 5:
    print("Bad arguments")
    sys.exit(1)

  normalData = NormalData(sys.argv[1])
  extraData = ExtraData(sys.argv[2])
  betterData = BetterData(sys.argv[3])
  slack = int(sys.argv[4])
  for normal in normalData:
    normalTime = int(normal[0])
    for extra in extraData:
      extraTime = int(extra[0])
      if normalTime > extraTime:
        print("Got unexpected extradata entry" + " ".join(extra))
        continue
      if normalTime + slack < extraTime:
        print("Got a data entry without extradata " + " ".join(normal))
        extraData.keepCurrent()
        break
      normal.extend(extra)
      betterData.writeLine(normal)
      break
  

if __name__ == "__main__":
  main()
