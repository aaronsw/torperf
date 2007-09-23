/* Copyright 2003 Roger Dingledine
 * Copyright 2004-2007 Roger Dingledine, Nick Mathewson
 * Copyright 2007 Roger Dingledine, Nick Mathewson, Steven J. Murdoch */
/* See LICENSE for licensing information */
/* $Id$ */

/**
 * Utility functions (based on src/common/util.h from Tor)
 */

#ifndef UTIL_H
#define UTIL_H

#include <stdlib.h>
#include <stdint.h>

#define INET_NTOA_BUF_LEN 16 /* 255.255.255.255 */

int write_all(int fd, const char *buf, size_t count, int isSocket);
int read_all(int fd, char *buf, size_t count, int isSocket);

uint16_t get_uint16(const char *cp);
uint32_t get_uint32(const char *cp);
void set_uint16(char *cp, uint16_t v);
void set_uint32(char *cp, uint32_t v);

int parse_addr_port(int severity, const char *addrport, char **address,
		    uint32_t *addr, uint16_t *port_out);

long parse_long(const char *s, int base, long min, long max,
		int *ok, char **next);

int strcasecmpend(const char *s1, const char *s2);

#endif // !UTIL_H
