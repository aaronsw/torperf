### Copyright 2007 Steven J. Murdoch
### See LICENSE for licensing information

UFACTOR = 1e6

## Subtract to timevals, maintaining precision
todelta <- function(startsec, startusec, tsec, tusec) {
  tsec[tsec == 0] <- NA
  dsec <- tsec - startsec
  dusec <- tusec - startusec
  return(dsec*UFACTOR + dusec)
}


parsedata <- function(filename, size) {

  filename <- paste("data/run2/", filename, sep="")
  
  t = read.table(filename, header=TRUE)

  tStart <- t$startsec*UFACTOR + t$startusec
  dSocket <- todelta(t$startsec, t$startusec, t$socketsec, t$socketusec)
  dConnect <- todelta(t$startsec, t$startusec, t$connectsec, t$connectusec)
  dNegotiate <- todelta(t$startsec, t$startusec, t$negotiatesec, t$negotiateusec)
  dRequest <- todelta(t$startsec, t$startusec, t$requestsec, t$requestusec)
  dResponse <- todelta(t$startsec, t$startusec, t$responsesec, t$responseusec)
  dDRequest <- todelta(t$startsec, t$startusec, t$datarequestsec, t$datarequestusec)
  dDResponse <- todelta(t$startsec, t$startusec, t$dataresponsesec, t$dataresponseusec)
  dDComplete <- todelta(t$startsec, t$startusec, t$datacompletesec, t$datacompleteusec)
  cbWrite <- t$writebytes
  cbRead <- t$readbytes
  
  results <- data.frame(tStart, dSocket, dConnect,
                        dNegotiate, dRequest, dResponse,
                        dDRequest, dDResponse, dDComplete,
                        cbWrite, cbRead)

  invalid <- abs(results$cbRead - size) > 64
  results[invalid,] <- NA
  
  return(results)
}

plotdist <- function(data, factor, labels, title, ylim=c(NA,NA)) {
  ## Scale units
  if (factor == 1e6)
    ylab <- "Time (s)"
  else if (factor == 1e3)
    ylab <- "Time (ms)"
  else {
    ylab <- "Time (us)"
    factor <- 1
  }

  d <- na.omit(data)/factor

  ## Find plotting range
  MinY<- NULL
  MaxY <- NULL

  range <- 1.5
  
  for (col in d) {
    s <- summary(col)
    Q1 <- as.vector(s[2])
    Q3 <- as.vector(s[5])
    InterQ <- Q3-Q1
    a <- Q1 - range*InterQ
    b <- Q3 + range*InterQ

    if (is.null(MinY) || a<MinY)
      MinY <- a

    if (is.null(MaxY) || b>MaxY)
      MaxY <- b
  }

  if (!is.na(ylim[1]))
      MinY <- ylim[1]
      
  if (!is.na(ylim[2]))
      MaxY <- ylim[2]

  ## Find how many points this will cause to be skipped
  skipped <- vector()
  for (i in (1:length(d))) {
    col <- d[[i]]
    isSkipped <- col<MinY | col>MaxY
    d[[i]][isSkipped] <- NA
    s <- length(which(isSkipped))
    ss <- paste("(",s,")",sep="")
    skipped <- append(skipped, ss)
  }

  labels <- mapply(paste, labels, skipped)
  if (length(d)>1)
    title <- paste(title, " (", length(d[[1]]), " runs)", sep="")
  else
    title <- paste(title, " (", length(d[[1]]), " runs, ", s, " skipped)", sep="")
  
  ## Plot the data
  boxplot(names=labels, d, frame.plot=FALSE, ylab=ylab, range=range,
          ylim=c(MinY, MaxY), xlab="Event (# points omitted)", main=title,
          pars=list(show.names=TRUE, boxwex = 0.8, staplewex = 0.5, outwex = 0.5))
}

first <- parsedata("first-big.data", 1048869)
second <- parsedata("second-big.data", 1048868)

EventNames <- c("start",
                "socket()", "connect()", "auth", "SOCKS req", "SOCKS resp",
                "HTTP req", "HTTP resp", "HTTP done")

png("first-local.png", width=800, height=533, bg="transparent")
par(mar=c(4.3,4.1,3.1,0.1))
plotdist(first[2:5], 1e3, EventNames[2:5], "Local events -- first request", c(0,2))
dev.off()

png("second-local.png", width=800, height=533, bg="transparent")
par(mar=c(4.3,4.1,5.1,0.1))
plotdist(second[2:5], 1e3, EventNames[2:5], "Local events -- second request", c(0,2))
dev.off()

png("first-net.png", width=800, height=533, bg="transparent")
par(mar=c(4.3,4.1,3.1,0.1))
plotdist(first[6:8], 1e6, EventNames[6:8], "Network events -- first request", c(0,8))
dev.off()

png("second-net.png", width=800, height=533, bg="transparent")
par(mar=c(4.3,4.1,5.1,0.1))
plotdist(second[6:8], 1e6, EventNames[6:8], "Network events -- second request", c(0,8))
dev.off()

png("first-download.png", width=600, height=533, bg="transparent")
par(mar=c(0.3,4.1,3.1,0.1))
plotdist(first[9], 1e6, EventNames[9], "HTTP download -- first request", c(0,150))
dev.off()

png("second-download.png", width=600, height=533, bg="transparent")
par(mar=c(0.3,4.1,3.1,0.1))
plotdist(second[9], 1e6, EventNames[9], "HTTP download -- second request", c(0,150))
dev.off()
