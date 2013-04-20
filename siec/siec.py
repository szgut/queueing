#!/usr/bin/env pypy
# -*- coding: utf-8 -*-
import dl24.connection
from dl24.misc import Serializer
from dl24.misc import delay_sigint
from dl24.colors import warn, bad, good, info, color, MAGENTA
import argparse
import traceback
import collections
import heapq
import sys
import multiprocessing

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
	# parser.add_argument("--double", action='store_true', 
	# 	help="double solve()")
	parser.add_argument("-A", "--accurate", action='store_true',
		help="compute accurate dijkstra")
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
		if self.same(a, b): return
		#if a == b: return
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

# def make_graph():
# 	return [ [ adjacent(Point(i, j)) for j in xrange(L)] for i in xrange(L) ]






def fee1(place):
	city_cost = 1
	k = 1000000
	if place in saturated:
		return C*k*fee[place.i][place.j] or city_cost
	return k*fee[place.i][place.j] or city_cost

def fee0(place):
	return fee[place.i][place.j] * (1 if place in permissions else C)


def feeA(place):
	city_cost = 1
	k = 1000000
	return k*fee0(place) or city_cost


def current_score():
	return sum(map(fee0, plan))



def dumpsplot(items, path):
	with open(path, 'w') as f:
		for i,j in allij():
				print>>f, i, j, items[i][j]

def dumpfees(plan, uni):
	with open("fees%d"%uni, 'w') as fs:
		with open("satu%d"%uni, 'w') as st:
			with open("cit%d"%uni, 'w') as ct:
				for place in plan:
					if place in cities:
						print>>ct, place.i, place.j, fee0(place)
					elif place not in saturated:
						print>>fs, place.i, place.j, fee0(place)
					else:
						print>>st, place.i, place.j, fee0(place)



def dumppoints(items, path):
	with open(path, 'w') as f:
		for point in items: 
			print>>f, point.i, point.j




def dijkstra_dists(city):
	feeN = feeA if args.accurate else fee1
	done = set()
	results = tdarr(lambda i,j: 10**12)
	results[city.i][city.j] = feeN(city)
	heap = [(feeN(city), city)]
	while heap:
		dist, pt = heapq.heappop(heap)
		if results[pt.i][pt.j] < dist: continue
		done.add(pt)

		for neigh in adjacent(pt):
			if neigh in done: continue
			nneighdist = dist + feeN(neigh)
			if nneighdist < results[neigh.i][neigh.j]:
				results[neigh.i][neigh.j] = nneighdist
				heapq.heappush(heap, (nneighdist, neigh))
	dot()
	return results


def dijkstra_route(city, dest, dijkstras):
	feeN = feeA if args.accurate else fee1
	results = dijkstras[dest.i][dest.j]
	# yield city
	while city != dest:
		dist_city = results[city.i][city.j]
		for neigh in adjacent(city):
			# if!
			# if fu._size(neigh) > 1 and not fu.same(city, neigh):
			# 	yield neigh
			# 	break
			boss = fu.boss[neigh.i][neigh.j]
			if fu._size(boss) > 1:
				fu.merge(city, neigh)

			dist_neigh = results[neigh.i][neigh.j]
			if dist_neigh + feeN(city) == dist_city:
				yield neigh
				city = neigh
	# if city==dest:
	# 	yield dest


def dot():
	sys.stdout.write(".")
	sys.stdout.flush()

def compute_dijkstras():
	results = tdarr(lambda i,j: 0)
	print "czekaj na dajkstrę", args.accurate
	with delay_sigint():
		pool = multiprocessing.Pool(3)
		dix = pool.map(dijkstra_dists, cities)
		pool.close()
	for a, dij in zip(cities, dix):
		results[a.i][a.j] = dij
	print
	return results





point_comp = lambda point: (-min(maxrequests[point.i][point.j],4), fee0(point))
def sort_used_points():
	used_points.sort(key=point_comp)

def update_permissions():
	new_reservations = conn.last_obtained()[0]
	with delay_sigint():
		for i,j in new_reservations:
			maxrequests[i][j] -= 1
			if maxrequests[i][j] <= 0:
				maxrequests[i][j] = 10000
				point = Point(i,j)
				if point not in permissions:
					saturated.add(Point(i, j))
	sort_used_points()

def solve(): #										<==========================================================
	global plan, used_points, fu
	fu = FindUnion()
	dijkstras = compute_dijkstras()
	
	# licz odległości między wszystkimi parami miast
	cities_dists = []
	for a in cities:
		dists_a = dijkstras[a.i][a.j]
		for b in cities:
			#cities_dists.append((dists_a[b.i][b.j], a, b))
			heapq.heappush(cities_dists, (dists_a[b.i][b.j], a, b))
	#cities_dists.sort()

	# dumpsplot(dijkstra_results[cities[0].i][cities[0].j], "dists")


	print "czekaj na routy"
	plan = []
	while cities_dists:
		dist, a, b = heapq.heappop(cities_dists)
	#for dist, a, b in cities_dists:
		if not fu.same(a, b):
			route = list(dijkstra_route(a, b, dijkstras))
			for r in route:
				fu.merge(a,r)
				for c in cities:
					heapq.heappush(cities_dists, (dijkstras[c.i][c.j][r.i][r.j], r, c))
			plan.extend(route)
			#plan.extend(dijkstra_route(a, b, dijkstras))
			dot()
			fu.merge(a,b)
			# fu.merge(a, route[-1])
	print
	plan.extend(cities)
	plan = set(plan)

	
	dumppoints(cities, "cities%d" % args.universum)
	dumppoints(plan, "plan%d" % args.universum)

	conn.declare_plan(plan)

	
	used_points = [point for point in plan if point not in saturated and point not in permissions]
	sort_used_points()


def obtain_permission():
	while used_points:
		point = used_points.pop()
		if point in permissions or point in saturated:
			continue
		try:
			print "trying", point, point_comp(point)
			conn.request(point)
		except dl24.connection.CommandFailedError as exc:
			if exc.errno == 107:
				print "adding %s to saturated" % str(point)
				with delay_sigint():
					saturated.add(point)
		else:
			print good("obtained permission for %s worth %d" % (str(point), fee0(point)))
			permissions.add(point)
			# if maxrequests[point.i][point.j] >= 20: # odpal dijkstrę
			# 	return False
			return True
	print "no more used_points:", len(used_points)
	return False




def new_world(loadstate=False, leave_accurate=False):
	global L,N,D,C,fee,maxrequests,saturated # pickled
	global cities, permissions # computed
	print info("new world")
	
	if loadstate:
		with delay_sigint():
			L,N,D,C, fee, maxrequests, saturated = serializer.load()
	else:
		world_description = conn.describe_world()
		with delay_sigint():
			(L,N,D,C,W,T,K), fee, maxrequests = world_description
		saturated = set()
	
	print "params:", L, N, D, C
	cities = [Point(i, j) for i,j in allij() if fee[i][j] == 0]
	
	permissions = set(cities)
	for point in conn.my_requests():
		permissions.add(point)

	if not leave_accurate:
		args.accurate = False
	# if not loadstate or args.recompute:
	# 	dijkstras = compute_dijkstras()


def print_high_scores():
	score = current_score()
	scstr = color(MAGENTA, str(score))
	ranks = conn.get_ranking()[:10]
	print "scores:",
	for rank in ranks:
		if rank==score:
			print scstr,
		else:
			print rank,
	print "" if score in ranks else "... " + scstr


# def ddist(a, b):
# 	return dijkstras[a.i][a.j][b.i][b.j]

if __name__ == '__main__':
	args = parse_args()
	config = Config(args.universum)
	serializer = Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	print info("connected.")

	new_world(args.loadstate, leave_accurate=True)


	time_left = conn.time_to_request()
	score = 10**9
	was_prog = False

	try:
		while 1:
			# new world, compute spanning tree
			solve()
			old_score = score
			score = current_score()
			print "score:", score

			while 1:
				# dokonuj rezerwacji
				if used_points or was_prog:
					was_prog = obtain_permission()
					if not was_prog:
						break
				print_high_scores()

				# sprawdź licznik rund
				old_time_left = time_left
				time_left = conn.time_to_request()
				print "to end:", time_left
				if time_left > old_time_left: # nowa runda!
					new_world()
					break
				# if time_left < 20 and not args.accurate: # mało czasu, licz dokładny wynik!
				# 	args.accurate = True
				# 	break
								
				print "used points left: %d" % len(used_points)
				dumpfees(plan, args.universum)

				update_permissions()
				conn.wait()

	except KeyboardInterrupt:
		serializer.save((L,N,D,C, fee, maxrequests, saturated))
	except:
		traceback.print_exc()
		serializer.save((L,N,D,C, fee, maxrequests, saturated), ".crash")
