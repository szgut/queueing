#!/usr/bin/env pypy
# -*- coding: utf-8 -*-
import dl24.connection
from dl24.misc import Serializer
from dl24.misc import delay_sigint
from dl24.colors import warn, bad, good, info
import argparse
import traceback
import collections
import heapq
import sys

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
	
	def request(self, point):
		self.cmd("REQUEST", point.i+1, point.j+1)

	def declare_plan(self, plan):
		try:
			self.cmd("DECLARE_PLAN", len(plan), [(i+1,j+1) for i,j in plan])
		except dl24.connection.CommandFailedError:
			pass
		else:
			print good("plan accepted")

	def _get_requests(self):
		s = self.readint()
		l = []
		for _ in xrange(s):
			l.append(Point(self.readint()-1, self.readint()-1))
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
	parser.add_argument("-R", "--recompute", action='store_true', 
		help="recompute dijkstras")
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






def fee1(city):
	if city in permissions:
		return 1
	if city in saturated:
		return (fee[city.i][city.j] or 1) * 10
	return fee[city.i][city.j] or 1


def dumpsplot(items, path):
	with open(path, 'w') as f:
		for i,j in allij():
				print>>f, i, j, items[i][j]

def dumpfees(plan, path):
	with open(path, 'w') as f:
		for place in plan:
			print>>f, place.i, place.j, fee1(place)



def dumppoints(items, path):
	with open(path, 'w') as f:
		for point in items: 
			print>>f, point.i, point.j





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


def dijkstra_dists(city):
	done = set()
	results = tdarr(lambda i,j: 10**9)
	results[city.i][city.j] = fee1(city)
	heap = [(fee1(city), city)]
	while heap:
		dist, pt = heapq.heappop(heap)
		if results[pt.i][pt.j] < dist: continue
		done.add(pt)

		for neigh in adjacent(pt):
			if neigh in done: continue
			nneighdist = dist + fee1(neigh)
			if nneighdist < results[neigh.i][neigh.j]:
				results[neigh.i][neigh.j] = nneighdist
				heapq.heappush(heap, (nneighdist, neigh))

	return results


def dijkstra_route(city, dest):
	results = dijkstras[dest.i][dest.j]
	while city != dest:
		dist_city = results[city.i][city.j]
		for neigh in adjacent(city):
			dist_neigh = results[neigh.i][neigh.j]
			if dist_neigh + fee1(city) == dist_city:
				yield neigh
				city = neigh


def dot():
	sys.stdout.write(".")
	sys.stdout.flush()

def compute_dijkstras():
	results = tdarr(lambda i,j: 0)
	print "czekaj na dajkstrę"
	for a in cities:
		results[a.i][a.j] = dijkstra_dists(a)
		dot()
	print
	return results


def solve():
	global used_points, plan
	fu = FindUnion()
	
	# licz odległości między wszystkimi parami miast
	cities_dists = []
	for a in cities:
		dists_a = dijkstras[a.i][a.j]
		for b in cities:
			cities_dists.append((dists_a[b.i][b.j], a, b))
	cities_dists.sort()

	# dumpsplot(dijkstra_results[cities[0].i][cities[0].j], "dists")

	print "czekaj na routy"
	plan = []
	for dist, a, b in cities_dists:
		if not fu.same(a, b):
			#plan.extend(dfs_route(a, b))
			plan.extend(dijkstra_route(a, b))
			dot()
			# plan.extend(dijkstra_route(dijkstra_results[b.i][b.j], a, b))
			fu.merge(a,b)
	print
	plan.extend(cities)
	plan = set(plan)

	
	dumppoints(cities, "cities%d" % args.universum)
	dumppoints(plan, "plan%d" % args.universum)

	conn.declare_plan(plan)

	used_points = sorted(plan, key=fee1)


def obtain_permission():
	while used_points:
		point = used_points.pop()
		if point in permissions:
			continue
		try:
			print "trying", point
			conn.request(point)
		except dl24.connection.CommandFailedError as exc:
			if exc.errno == 107:
				print "adding %s to saturated" % str(point)
				saturated.add(point)
		else:
			print good("obtained permission for %s worth %d" % (str(point), fee1(point)))
			permissions.add(point)
			return
	print "no more used_points"




def new_world(loadstate=False, recompute=False):
	global L,N,D,fee,maxrequests,dijkstras,saturated
	global cities, permissions
	print info("new world")
	
	if loadstate:
		L,N,D, fee, maxrequests, dijkstras, saturated = serializer.load()
	else:
		(L,N,D,C,W,T,K), fee, maxrequests = conn.describe_world()
		saturated = set()
	
	print "params:", L, N, D
	cities = [Point(i, j) for i,j in allij() if fee[i][j] == 0]
	
	permissions = set(cities)
	for point in conn.my_requests():
		permissions.add(point)
		
	if not loadstate or args.recompute:
		dijkstras = compute_dijkstras()

		


# def ddist(a, b):
# 	return dijkstras[a.i][a.j][b.i][b.j]

if __name__ == '__main__':
	args = parse_args()
	config = Config(args.universum)
	serializer = Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	print info("connected.")

	new_world(args.loadstate, args.recompute)


	time_left = conn.time_to_request()
	try:
		while 1:
			# new world, compute spanning tree
			solve()

			while 1:
				obtain_permission()
				print "used points left: %d" % len(used_points)
				
				old_time_left = time_left
				time_left = conn.time_to_request()
				if time_left > old_time_left:
					new_world()
					break
				else:
					print "to end:", time_left
					dumpfees(plan, "fees%d" % args.universum)
					conn.wait()

	except KeyboardInterrupt:
		serializer.save((L,N,D, fee, maxrequests, dijkstras, saturated))
	except:
		traceback.print_exc()
		serializer.save((L,N,D, fee, maxrequests, dijkstras, saturated), ".crash")
