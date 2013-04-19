#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import dl24.connection
from dl24.misc import Serializer
from dl24.misc import delay_sigint
from dl24.colors import warn, bad, good, info
import argparse
import traceback
import collections

class Config(object):
	def __init__(self, universum=1):
		self.host = 'universum.dl24'
		self.datafile = 'data%d' % universum
		self.port = 20002 + universum-1
		self.limitD = 1000 if universum == 2 else None

class Connection(dl24.connection.Connection):
	def __init__(self, host='universum.dl24', port=20002):
		super(Connection, self).__init__(host, port)
	# implementacja komend z zadania
	
	def describe_world(self):
		self.cmd("DESCRIBE_WORLD")
		params = self.readints(6)
		params.append(self.readfloat())
		L = params[0]
		fees = [self.readints(L) for _ in xrange(L)]
		maxrequests = [self.readints(L) for _ in xrange(L)]
		return (params, fees, maxrequests)

	def time_to_request(self):
		self.cmd("TIME_TO_REQUEST")
		return self.readint()
	
	def request(self, i, j):
		self.cmd("REQUEST", i, j)

	def declare_plan(self, plan):
		self.cmd("DECLARE_PLAN", len(plan), "\n", plan)

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

	def get_ranking(self):
		self.cmd("GET_RANKING")
		s = self.readint()
		return self.readints(s)


def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-U", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-D", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	return parser.parse_args()

####################################################################################################

def new_world():
	global L,N,D,fees,maxrequests
	print info("new world")
	(L,N,D,C,W,T,K), fees, maxrequests = conn.describe_world()

def init_state(loadstate):
	global L,N,D,fees,maxrequests
	if loadstate:
		L,N,D, fees, maxrequests = serializer.load()
	else:
		new_world()
		


Place = collections.namedtuple('Place', ['i', 'j'])
def dist(placea, placeb):
	pass


def turn():
	pass	


def dumpfees(path="fees"):
	with open(path, 'w') as f:
		for i in xrange(L):
			for j in xrange(L):
				if fees[i][j] < 400:
					print>>f, i, j, fees[i][j]

if __name__ == '__main__':
	args = parse_args()
	config = Config(args.universum)
	serializer = Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	print info("connected.")

	init_state(args.loadstate)
	print L,N,D
	# dumpfees()

	try: # main loop
		while 1:
			turn()
			old_time_left = time_left
			time_left = conn.time_to_request()
			if time_left > old_time_left
				new_world()
			else:
				time_left = curr_time_left
				conn.wait()
	except KeyboardInterrupt:
		serializer.save((L,N,D, fees, maxrequests))
	except:
		traceback.print_exc()
		serializer.save((L,N,D, fees, maxrequests), ".crash")
