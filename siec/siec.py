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

Point = collections.namedtuple('Point', ['i', 'j'])

class Connection(dl24.connection.Connection):
	def __init__(self, host='universum.dl24', port=20002):
		super(Connection, self).__init__(host, port)
	# implementacja komend z zadania
	
	def describe_world(self):
		self.cmd("DESCRIBE_WORLD")
		params = self.readints(6)
		params.append(self.readfloat())
		L = params[0]
		fee = [self.readints(L) for _ in xrange(L)]
		maxrequests = [self.readints(L) for _ in xrange(L)]
		return (params, fee, maxrequests)

	def time_to_request(self):
		self.cmd("TIME_TO_REQUEST")
		return self.readint()
	
	def request(self, i, j):
		self.cmd("REQUEST", i, j)

	def declare_plan(self, plan):
		self.cmd("DECLARE_PLAN", len(plan), [(i+1,j+1) for i,j in plan])

	def _get_requests(self):
		s = self.readint()
		l = []
		for _ in xrange(s):
			l.append(Point(self.readint(), self.readint()))
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
####################################################################################################
####################################################################################################

def tdarr(fun):
	return [[fun(i, j) for j in xrange(L)] for i in xrange(L)]


class FindUnion(object):
	def __init__(self):
		self.size = tdarr(lambda i,j: 1)
		self.boss = tdarr(Point)

	def _root(self, i, j):
		cboss = self.boss[i][j]
		if cboss != Point(i,j):
			self.boss[i][j] = self._root(cboss.i, cboss.j)
		return self.boss[i][j]

	def _size(self, point):
		return self.size[point.i][point.j]

	def merge(self, a, b):
		if a == b: return
		a, b = self._root(a.i, a.j), self._root(b.i, b.j)
		if self._size(a) > self._size(b):
			self.boss[b.i][b.j] = a
		else:
			self.boss[a.i][a.j] = b
			if self._size(a) == self._size(b):
				self.size[b.i][b.j] += 1

	def same(self, a, b):
		return self._root(a.i, a.j) == self._root(b.i, b.j)


def allij():
	for i in xrange(L):
		for j in xrange(L):
			yield (i, j)

def new_world(loadstate=False):
	global L,N,D,fee,maxrequests
	global cities
	print info("new world")
	
	if loadstate:
		L,N,D, fee, maxrequests = serializer.load()
	else:
		(L,N,D,C,W,T,K), fee, maxrequests = conn.describe_world()
	
	cities = [Point(i, j) for i,j in allij() if fee[i][j] == 0]

		


def owned():
	points = list(cities)
	points.extend(conn.my_requests())
	return points

def turn():
	pass	


def dumpfees(path="fees"):
	with open(path, 'w') as f:
		for i,j in allij():
			if fee[i][j] < 100:
				print>>f, i, j, maxrequests[i][j]


def dumppoints(items, path):
	with open(path, 'w') as f:
		for point in items: 
			print>>f, point.i, point.j



def adjacent(point):
	def isok(point):
		return 0 <= point.i < L and 0 <= point.j < L
	def sasiedzi(point):
		if point.i % 2 == 0: # NP
			yield Point(point.i, point.j+1)
			yield Point(point.i, point.j-1)
			yield Point(point.i-1, point.j)
			yield Point(point.i-1, point.j-1)
			yield Point(point.i+1, point.j)
			yield Point(point.i+1, point.j-1)
		else:	# P
			yield Point(point.i, point.j+1)
			yield Point(point.i, point.j-1)
			yield Point(point.i-1, point.j+1)
			yield Point(point.i-1, point.j)
			yield Point(point.i+1, point.j+1)
			yield Point(point.i+1, point.j)
	return filter(isok, sasiedzi(point))

def make_graph():
	return [ [ adjacent(Point(i, j)) for j in xrange(L)] for i in xrange(L) ]


def dfs_dist(pointa, pointb):
	return abs(pointa.i - pointb.i) + abs(pointa.j - pointb.j)

def dfs_route(pointa, pointb):
	''' returns points between pointa and pointb (excluding) '''
	dj = 1 if pointb.j > pointa.j else -1
	di = 1 if pointb.i > pointa.i else -1
	for j in xrange(pointa.j+dj, pointb.j+dj, dj):
		yield Point(pointa.i, j)
	for i in xrange(pointa.i+di, pointb.i, di):
		yield Point(i, pointb.j)


if __name__ == '__main__':
	args = parse_args()
	config = Config(args.universum)
	serializer = Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	print info("connected.")

	new_world(args.loadstate)
	print L,N,D
	print conn.get_ranking()
	print len(cities), N

	plan = []
	fu = FindUnion()
	cities_dists = [(dfs_dist(a,b), a, b) for a in cities for b in cities]
	cities_dists.sort()
	mcount = 0
	for dist, a, b in cities_dists:
		if not fu.same(a, b):
			plan.extend(dfs_route(a, b))
			print "joining", list(a), b
			fu.merge(a,b)
			mcount += 1
	plan.extend(cities)
	print mcount

	dumppoints(cities, "cities")
	dumppoints(set(plan), "plan")

	conn.declare_plan(set(plan))

	# print len(owned()), N
	# print conn.get_ranking()


	time_left = conn.time_to_request()
	try: # main loop
		while 1:
			turn()
			
			old_time_left = time_left
			time_left = conn.time_to_request()
			if time_left > old_time_left:
				new_world()
			else:
				print time_left
				conn.wait()

	except KeyboardInterrupt:
		serializer.save((L,N,D, fee, maxrequests))
	except:
		traceback.print_exc()
		serializer.save((L,N,D, fee, maxrequests), ".crash")
