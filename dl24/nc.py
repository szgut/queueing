#!/usr/bin/env python
import readline
import sys

from dl24 import connection


def main(host, sport):
	conn = connection.Connection(host, int(sport))
	try:
		while True:
			line = raw_input('> ')
			if line:
				conn.cmd(line.upper())
			try:
				print conn.readline()
			except KeyboardInterrupt:
				pass
	except (EOFError, KeyboardInterrupt):
		pass

if __name__ == '__main__':
	try:
		readline.read_history_file()
	except IOError:
		print>>sys.stderr, 'touchnij se ~/.history'
	main(*sys.argv[1:])
	readline.write_history_file()