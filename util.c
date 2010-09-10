/* Copyright 2003 Roger Dingledine
 * Copyright 2004-2007 Roger Dingledine, Nick Mathewson
 * Copyright 2007 Roger Dingledine, Nick Mathewson, Steven J. Murdoch */
/* See LICENSE for licensing information */

/**
 * Utility functions (based on src/common/util.c from Tor)
 */

#define _GNU_SOURCE

#include "util.h"

#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <stdint.h>
#include <assert.h>
#include <string.h>
#include <netdb.h>
#include <stdio.h>

#define SIZE_T_CEILING (sizeof(char)<<(sizeof(size_t)*8 - 1))

/** Write <b>count</b> bytes from <b>buf</b> to <b>fd</b>.  <b>isSocket</b>
 * must be 1 if fd was returned by socket() or accept(), and 0 if fd
 * was returned by open().  Return the number of bytes written, or -1
 * on error.  Only use if fd is a blocking fd.  */
int
write_all(int fd, const char *buf, size_t count, int isSocket)
{
  size_t written = 0;
  int result;

  while (written != count) {
    if (isSocket)
      result = send(fd, buf+written, count-written, 0);
    else
      result = write(fd, buf+written, count-written);
    if (result<0)
      return -1;
    written += result;
  }
  return count;
}

/** Read from <b>fd</b> to <b>buf</b>, until we get <b>count</b> bytes
 * or reach the end of the file. <b>isSocket</b> must be 1 if fd
 * was returned by socket() or accept(), and 0 if fd was returned by
 * open().  Return the number of bytes read, or -1 on error. Only use
 * if fd is a blocking fd. */
int
read_all(int fd, char *buf, size_t count, int isSocket)
{
  size_t numread = 0;
  int result;

  if (count > SIZE_T_CEILING)
    return -1;

  while (numread != count) {
    if (isSocket)
      result = recv(fd, buf+numread, count-numread, 0);
    else
      result = read(fd, buf+numread, count-numread);
    if (result<0)
      return -1;
    else if (result == 0)
      break;
    numread += result;
  }
  return numread;
}

/**
 * Read a 16-bit value beginning at <b>cp</b>.  Equivalent to
 * *(uint16_t*)(cp), but will not cause segfaults on platforms that forbid
 * unaligned memory access.
 */
uint16_t
get_uint16(const char *cp)
{
  uint16_t v;
  memcpy(&v,cp,2);
  return v;
}
/**
 * Read a 32-bit value beginning at <b>cp</b>.  Equivalent to
 * *(uint32_t*)(cp), but will not cause segfaults on platforms that forbid
 * unaligned memory access.
 */
uint32_t
get_uint32(const char *cp)
{
  uint32_t v;
  memcpy(&v,cp,4);
  return v;
}
/**
 * Set a 16-bit value beginning at <b>cp</b> to <b>v</b>. Equivalent to
 * *(uint16_t)(cp) = v, but will not cause segfaults on platforms that forbid
 * unaligned memory access. */
void
set_uint16(char *cp, uint16_t v)
{
  memcpy(cp,&v,2);
}
/**
 * Set a 32-bit value beginning at <b>cp</b> to <b>v</b>. Equivalent to
 * *(uint32_t)(cp) = v, but will not cause segfaults on platforms that forbid
 * unaligned memory access. */
void
set_uint32(char *cp, uint32_t v)
{
  memcpy(cp,&v,4);
}

/* Helper: common code to check whether the result of a strtol or strtoul or
 * strtoll is correct. */
#define CHECK_STRTOX_RESULT()                           \
  /* Was at least one character converted? */           \
  if (endptr == s)                                      \
    goto err;                                           \
  /* Were there unexpected unconverted characters? */   \
  if (!next && *endptr)                                 \
    goto err;                                           \
  /* Is r within limits? */                             \
  if (r < min || r > max)                               \
    goto err;                                           \
  if (ok) *ok = 1;                                      \
  if (next) *next = endptr;                             \
  return r;                                             \
 err:                                                   \
  if (ok) *ok = 0;                                      \
  if (next) *next = endptr;                             \
  return 0

/** Extract a long from the start of s, in the given numeric base.  If
 * there is unconverted data and next is provided, set *next to the
 * first unconverted character.  An error has occurred if no characters
 * are converted; or if there are unconverted characters and next is NULL; or
 * if the parsed value is not between min and max.  When no error occurs,
 * return the parsed value and set *ok (if provided) to 1.  When an error
 * occurs, return 0 and set *ok (if provided) to 0.
 */
long
parse_long(const char *s, int base, long min, long max,
	   int *ok, char **next)
{
  char *endptr;
  long r;

  r = strtol(s, &endptr, base);
  CHECK_STRTOX_RESULT();
}

/** Similar behavior to Unix gethostbyname: resolve <b>name</b>, and set
 * *<b>addr</b> to the proper IP address, in host byte order.  Returns 0
 * on success, -1 on failure; 1 on transient failure.
 *
 * (This function exists because standard windows gethostbyname
 * doesn't treat raw IP addresses properly.)
 */
int
lookup_hostname(const char *name, uint32_t *addr)
{
  struct hostent *hp;
  struct in_addr* myaddr;

  if ((hp = gethostbyname(name)) == NULL)
    return -1;

  if (hp->h_addrtype != AF_INET)
    return -1;

  myaddr = (struct in_addr*)(hp -> h_addr_list[0]);

  if (myaddr == NULL)
    return -1;

  *addr = ntohl(myaddr -> s_addr);

  return 0;
}

/** Parse a string of the form "host[:port]" from <b>addrport</b>.  If
 * <b>address</b> is provided, set *<b>address</b> to a copy of the
 * host portion of the string.  If <b>addr</b> is provided, try to
 * resolve the host portion of the string and store it into
 * *<b>addr</b> (in host byte order).  If <b>port_out</b> is provided,
 * store the port number into *<b>port_out</b>, or 0 if no port is given.
 * If <b>port_out</b> is NULL, then there must be no port number in
 * <b>addrport</b>.
 * Return 0 on success, -1 on failure.
 */
int
parse_addr_port(int severity, const char *addrport, char **address,
                uint32_t *addr, uint16_t *port_out)
{
  const char *colon;
  char *_address = NULL;
  int _port;
  int ok = 1;

  assert(addrport);

  colon = strchr(addrport, ':');
  if (colon) {
    _address = strndup(addrport, colon-addrport);
    _port = (int) parse_long(colon+1,10,1,65535,NULL,NULL);
    if (!_port) {
      fprintf(stderr, "Port %s out of range\n", colon+1);
      ok = 0;
    }
    if (!port_out) {
      fprintf(stderr, "Port %s given on %s when not required\n",
	      colon+1, addrport);
      ok = 0;
    }
  } else {
    _address = strdup(addrport);
    _port = 0;
  }

  if (addr) {
    /* There's an addr pointer, so we need to resolve the hostname. */
    if (lookup_hostname(_address,addr)) {
      fprintf(stderr, "Couldn't look up %s\n", _address);
      ok = 0;
      *addr = 0;
    }
  }

  if (address && ok) {
    *address = _address;
  } else {
    if (address)
      *address = NULL;
    free(_address);
  }
  if (port_out)
    *port_out = ok ? ((uint16_t) _port) : 0;

  return ok ? 0 : -1;
}

/** Compares the last strlen(s2) characters of s1 with s2.  Returns as for
 * strcasecmp.
 */
int
strcasecmpend(const char *s1, const char *s2)
{
  size_t n1 = strlen(s1), n2 = strlen(s2);
  if (n2>n1) /* then they can't be the same; figure out which is bigger */
    return strcasecmp(s1,s2);
  else
    return strncasecmp(s1+(n1-n2), s2, n2);
}

