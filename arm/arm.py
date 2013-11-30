#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import collections
import traceback
import threading
import random

from dl24 import connection
from dl24 import log
from dl24 import misc
from dl24 import slottedstruct
from dl24.worker import Point as workerPoint, Worker


class Config(object):
	def __init__(self, universum=1):
		self.host = 'arm'
		self.datafile = 'data.%d' % universum
		self.port = 7010 + universum


class Point(workerPoint):
	
	def neighs(self):
		yield Point(self.x, self.y+1)
		yield Point(self.x, self.y-1)
		yield Point(self.x-1, self.y)
		yield Point(self.x+1, self.y)
	


class Division(slottedstruct.SlottedStruct):
	__slots__ = ('point', 'n')
	
	def randdir(self):
		r = random.Random()
		dx, dy = 0,0
		while dx*dx + dy*dy != 1:
			dx = r.randint(-1,1)
			dy = r.randint(-1,1)
		return Point(self.point.x+dx, self.point.y+dy)
			


class Connection(connection.Connection):
	
	def money(self):
		self.cmd('GET_MY_MONEY')
		return self.readint()

	def divisions(self):
		self.cmd('GET_MY_TERRITORY')
		k = self.readint()
		return map(lambda *x: Division(Point(*self.readints(2)), self.readint()), xrange(k))
	
	def recruit_soldiers(self, point, s):
		self.cmd('RECRUIT_SOLDIERS', point.x, point.y, s)
	
	def move(self, fr, to, smax, smin):
		self.cmd('ATTACK_OR_TRANSFER', fr, to, smax, smin)
			
	def descrie_world(self):
		self.cmd('DESCRIBE_WORLD')
		return self.readints(3)
	
	def get_time(self):
		self.cmd('GET_TIME')
		return self.readints(3)
	
	def show_bonus(self, i):
		self.cmd('SHOW_BONUS', i)
		k = self.readint()
		return map(lambda *x: Point(*self.readints(2)), xrange(k))


def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-d", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	parser.add_argument('posargs', nargs='?', default=[])
	return parser.parse_args()





class WorldMap(object):
	def __init__(self, N):
		self.N = N
		self.swamps = set()
		self.read_bonuses()
		
	def is_swamp(self, point):
		if point.x < 1 or point.x > self.N or point.y < 1 or point.y > self.N:
			return True
		return point in self.swamps
	
	def set_swamp(self, point, value=True):
		if value:
			self.swamps.add(point)
		else:
			self.swamp.remove(point)
	
	def draw_swamps(self):
		worker.command(tid=100, points=map(tuple, self.swamps), color=(150,60,0))

	def read_bonuses(self):
		_, _, b = conn.descrie_world()
		self.bonuses = []
		self.bonus_map = collections.defaultdict(int)
		for i in xrange(1, b+1):
			bonus = conn.show_bonus(i)
			self.bonuses.append(bonus)
			for point in bonus:
				self.bonus_map[point] = i
			
	
	def draw_bonuses(self):
		empty_points, taken_points = [], []
		for bonus in self.bonuses:
			for point in bonus:
				if sol_count[point]:
					taken_points.append(tuple(point))
				else:
					empty_points.append(tuple(point))
		worker.command(tid=200, points=empty_points, color=(100, 100, 255))
		worker.command(tid=201, points=taken_points, color=(255, 0, 0))
	
	def my_bonuses(self):
		my = set()
		for i, bonus in enumerate(self.bonuses, 1):
			for point in bonus:
				if sol_count[point]:
					my.add(i)
					break
		return my

	@staticmethod
	def _taken_bonus(bonus):
		for point in bonus:
			if not sol_count[point]:
				return False
		return True 

	def good_bonuses(self):
		my = self.my_bonuses()
		good = []
		for i in my:
			if self._taken_bonus(self.bonuses[i-1]):
				good.append(i)
		return good


def init_state(read=False):
	global world_map, round_no, sol_count, layer_map
	if read:
		world_map, round_no = serializer.load()
	else:
		N, _, _ = conn.descrie_world()
		world_map = WorldMap(N)
		round_no, _, _ = conn.get_time()
	sol_count = collections.defaultdict(int)
	layer_map = collections.defaultdict(int)


class Clicker(threading.Thread):
	
	target = None
	
	def __init__(self):
		super(Clicker, self).__init__()
		self.daemon = True
	
	def run(self):
		while True:
			for click in worker.iterget():
				point = Point(*click.point)
				log.good("%s at %s, %d" % (sol_count[point], point, layer_map[point]))
				Clicker.target = point

def read_time():
	global round_no

	curr_round_no, turn_no, total_turns = conn.get_time()
	print 'round %d: %d/%d' % (curr_round_no, turn_no, total_turns)
	if curr_round_no > round_no:
		init_state()


def clustering(divisions, sol_count):
	clusters = []
	visited = set()
	
	def visit(point, cluster):
		if point in visited: return
		visited.add(point)
		cluster.add(point)
		for neigh in point.neighs():
			if sol_count[neigh]:
				visit(neigh, cluster)
		return cluster
	
	for div in divisions:
		cluster = visit(div.point, set())
		if cluster:
			clusters.append(cluster)
	return clusters


def layerize(cluster, sol_count, layer_map):
	que = collections.deque()
	for point in cluster:
		for neigh in point.neighs():
			if not world_map.is_swamp(neigh) and not sol_count[neigh]:
				que.append(point)
				layer_map[point] = 1
				break
	while que:
		point = que.popleft()
		clayer = layer_map[point]
		for neigh in point.neighs():
			if sol_count[neigh] and not layer_map[neigh]:
				layer_map[neigh] = clayer + 1
				que.append(neigh)

def recruit():
	money = conn.money()
	print 'money: %d' % money
	
	target = Clicker.target
	if target is not None and sol_count[target]:
		point = target
	else:
		edge = []
		for point, layer in layer_map.iteritems():
			if layer == 1:
				edge.append(point)
		point = random.Random().choice(edge)
	try:
		conn.recruit_soldiers(point, money)
		sol_count[point] += money
		print "recruited %d at %s" % (money, point)
	except connection.CommandFailedError as e:
		log.warn(e)
	

def choose_target(point, my_bonuses):
	neighs = []
	for neigh in point.neighs():
		if layer_map[neigh] < layer_map[point] and not world_map.is_swamp(neigh):
			neighs.append(neigh)
	random.Random().shuffle(neighs)
	
	if len(my_bonuses) <= 3:
		for neigh in neighs:
			if world_map.bonus_map[neigh] in my_bonuses:
				return neigh # defend!
		if len(my_bonuses) < 3:
			for neigh in neighs:
				if world_map.bonus_map[neigh]:
					return neigh # attack!
		for neigh in neighs:
			if not world_map.bonus_map[neigh]:
				return neigh
	else:
		for neigh in neighs:
			if not world_map.bonus_map[neigh]:
				return neigh # leave!
	return None
	

def loop():
	global sol_count, layer_map
	read_time()
	
	
	divisions = conn.divisions()
	
	# update sol_count	
	
	for div in divisions:
		sol_count[div.point] = div.n
	
	# compute clusters
	clusters = clustering(divisions, sol_count)
	# layerize
	
	for cluster in clusters:
		layerize(cluster, sol_count, layer_map)
	
	recruit()
	
	# draw
	for i, cluster in enumerate(clusters):
		strength = 0
		points = []
		for point in cluster:
			strength += sol_count[point]
			points.append(tuple(point))
		worker.command(tid=i, points=points, label=str(strength))
	for j in xrange(i+1, 40):
		worker.command(action='remove', tid=j)	

	world_map.draw_swamps()
	world_map.draw_bonuses()
	
	# move
	orders_count = 0
	permdiv = sorted(divisions, key=lambda div: div.n, reverse=True)
#	print permdiv[:5]
	my_bonuses = world_map.my_bonuses()
	for div in permdiv:
		if orders_count == 5: break
		if div.n == 1: break
		try:
			point = div.point	
			dest = choose_target(point, my_bonuses)
			if dest is not None:
				conn.move(point, dest, div.n, 1)
				print "moving from", point, layer_map[point], "to", dest, layer_map[dest], "strength", div.n
				orders_count += 1
		except connection.CommandFailedError as e:
			log.bad(e)
			if e.errno == 109:
				print dest, "is swamp"
				world_map.set_swamp(dest)
	
	print "my bonuses:", list(world_map.my_bonuses()), list(world_map.good_bonuses())
	
	

if __name__ == '__main__':
	args = parse_args()
	config = Config(args.universum)
	serializer = misc.Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	log.info("logged in")

	
	worker = Worker(title=('ARM-%d' % args.universum))
	Clicker().start()
	
	init_state(args.loadstate)
	
	try: # main loop
		while 1:
			loop()
			conn.wait()
	except KeyboardInterrupt:
		serializer.save([world_map, round_no])
	except:
		traceback.print_exc()
		serializer.save([world_map, round_no], ".crash")
