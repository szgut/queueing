#!/usr/bin/env python
import readline
import sys
import threading

from dl24 import connection


class Reader(threading.Thread):
	def __init__(self, conn):
		super(Reader, self).__init__()
		self.daemon = True
		self.conn = conn
	
	def run(self):
		while True:
			print self.conn.readline()


def main(host, sport):
	conn = connection.Connection(host, int(sport))
	Reader(conn).start()
	try:
		if  sport < 7021 or sport > 7022:
			while True:
				conn.writeln(raw_input().upper())
			else:
				ipu = raw_input()
				if ipu[:4] == "WAIT":
					
	except (EOFError, KeyboardInterrupt):
		pass

if __name__ == '__main__':
	try:
		readline.read_history_file()
	except IOError:
		print>>sys.stderr, 'touchnij se ~/.history'
	main(*sys.argv[1:])
	readline.write_history_file()
