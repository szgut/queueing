#ifndef __KRDLN_TCP_HPP__
#define __KRDLN_TCP_HPP__

#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <string.h>
#include <cstdio>

namespace krdln {
struct Socket {
	int fd;
	
	Socket(char const * host, char const * port) {
		int sock;
		addrinfo addr_hints;
		addrinfo *addr_result;
		
		int err;

		// 'converting' host/port in string to struct addrinfo
		memset(&addr_hints, 0, sizeof(addrinfo));
		addr_hints.ai_family = AF_INET; // IPv4
		addr_hints.ai_socktype = SOCK_STREAM;
		addr_hints.ai_protocol = IPPROTO_TCP;
		err = getaddrinfo(host, port, &addr_hints, &addr_result);
		if (err != 0) {
			fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(err));
			assert(false);
		}
		
		// initialize socket according to getaddrinfo results
		sock = socket(addr_result->ai_family, addr_result->ai_socktype, addr_result->ai_protocol);
		assert(sock >= 0);
		assert(connect(sock, addr_result->ai_addr, addr_result->ai_addrlen) >= 0);
		fd = sock;
	}
	
	~Socket() {
		close(fd);
	}
};
}
#endif
