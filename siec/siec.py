#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import dl24.connection
from dl24.misc import Serializer
from dl24.misc import delay_sigint
from dl24.colors import warn, bad, good, info
import argparse
import traceback

class Config(object):
	def __init__(self, universum=1):
		self.host = 'universum.dl24'
		self.datafile = 'data'
		self.port = 20002+universum-1
		self.limitD = 1000 if universum == 2 else None

class Connection(dl24.connection.Connection):
	# implementacja komend z zadania
	
	def time_to_request(self):
		self.cmd("TIME_TO_REQUEST")
		return self.readint()
	
	def request(self, i, j):
		self.cmd("REQUEST", i, j)

	def _get_requests(self):
		s = self.readint()
		l = []
		for _ in xrange(s):
			l.append((self.readint(), self.readint()))
		return l

	def my_requests(self):
		self.cmd("MY_REQUESTS")
		return self._get_requests()
	
	def last_obtained(self):
		self.cmd("LAST_OBTAINED")
		return [self._get_requests() for _ in xrange(5)]



def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-U", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-D", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	return parser.parse_args()

def init_state(read):
	global global_sth
	if read:
		global_sth = serializer.load()
	else:
		global_sth = 0


zmienna_statyczna = [1]
def loop():
	# ~import time
	# ~print "."
	zmienna_statyczna[0] += 1
	conn.cmd_dupa(zmienna_statyczna[0])
	# ~time.sleep(3)


if __name__ == '__main__':
	args = parse_args()
	config = Config(args.universum)
	serializer = Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	print info("logged in")

	init_state(args.loadstate)
	global_sth += 1
	print global_sth
	
	try: # main loop
		while 1:
			loop()
			conn.wait()
	except KeyboardInterrupt:
		serializer.save(global_sth)
	except:
		traceback.print_exc()
		serializer.save(global_sth, ".crash")
