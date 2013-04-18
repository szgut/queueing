#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import dl24.connection
from dl24.misc import Serializer
from dl24.colors import warn, bad, good, info
import argparse
import traceback

class Config(object):
	def __init__(self, universum=1):
		self.host = 'localhost'
		self.datafile = 'data'
		self.port = 20000+universum-1

class Connection(dl24.connection.Connection):
	# implementacja komend z zadania
	def dupa(self):
		self.cmd_dupa(3, [4, 5])
		return self.readints(2)


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
		global_sth = serializator.load()
	else:
		global_sth = 0



def loop():
	import time
	print "."
	time.sleep(3)


if __name__ == '__main__':
	args = parse_args()
	config = Config(args.universum)
	serializer = Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	conn.login()
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
