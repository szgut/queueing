#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import traceback

from dl24 import connection
from dl24 import log
from dl24 import misc


class Config(object):
	def __init__(self, universum=1):
		self.host = 'localhost'
		self.datafile = 'data'
		self.port = 20000+universum-1


class Connection(connection.Connection):
	# implementacja komend z zadania
	def dupa(self):
		self.cmd("dupa", 3, [4, 5])
		return self.readints(2)


def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-d", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	parser.add_argument('posargs', nargs='*', default=[])
	return parser.parse_args()


class PersistentState(object):
	def __init__(self):
		self.a = 0


def init_state(read):
	global gs
	if read:
		gs = serializer.load()
	else:
		gs = PersistentState()


def loop():
	conn.dupa()


if __name__ == '__main__':
	args = parse_args()
	print args.posargs
	config = Config(args.universum)
	serializer = misc.Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	log.info("logged in")

	init_state(args.loadstate)
	gs.a += 1
	print gs.a
	
	try: # main loop
		while 1:
			loop()
			conn.wait()
	except KeyboardInterrupt:
		serializer.save(gs)
	except:
		traceback.print_exc()
		serializer.save(gs, ".crash")
