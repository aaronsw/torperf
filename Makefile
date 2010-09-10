### Copyright 2007 Steven J. Murdoch
### See LICENSE for licensing information

CC=gcc -Wall -Werror -ggdb
R=R CMD BATCH --vanilla
IMAGES=first-download.png first-local.png first-net.png second-download.png second-local.png second-net.png

all: trivsocks-client

trivsocks-client: trivsocks-client.o util.o
	$(CC) -o $@ $^

%.o: %.c
	$(CC) -c $<

test: trivsocks-client
	./trivsocks-client -4 tor.eff.org /
	./trivsocks-client -5 tor.eff.org /

$(IMAGES): plot_results.R
	$(R) $<

clean:
	rm -f *~ *.o trivsocks-client *.png *.Rout
