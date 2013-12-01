#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import collections
import traceback
import time
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
	
	def get_field(self, point):
		self.cmd('GET_FIELD', point.x, point.y)
		k = self.readint()
		enemies_around = {}
		for _ in xrange(k):
			point = Point(*self.readints(2))
			enemies_around[point] = self.readint()
			self.readint()
		return enemies_around
	
	def get_turn_result(self):
		self.cmd('GET_TURN_RESULT')
		k = self.readint()
		points = []
		for _ in xrange(k):
			points.append(Point(*self.readints(2)))
			self.readints(2)
		return points
		


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
		good = set()
		for i in my:
			if self._taken_bonus(self.bonuses[i-1]):
				good.add(i)
		return good
	
	def get_bonus(self, i):
		return self.bonuses[i-1]


def init_state(read=False):
	global world_map, round_no, clusters
	if read:
		world_map, round_no = serializer.load()
	else:
		N, _, _ = conn.descrie_world()
		world_map = WorldMap(N)
		round_no, _, _ = conn.get_time()
	clusters = []


def get_enemies(point, _conn=None):
	cconn = _conn or conn
	for neigh in point.neighs():
		if not sol_count[neigh]: continue
		enemies_around = cconn.get_field(neigh)
		for enpoint, value in enemies_around.iteritems():
			if enpoint == point:
				return value
	return None


class Clicker(threading.Thread):
	
	target = None
	
	def __init__(self):
		super(Clicker, self).__init__()
		self.daemon = True
		self._conn = Connection(config.host, config.port)
	
	def run(self):
		while True:
			for click in worker.iterget():
				point = Point(*click.point)
				if click.button == 1:
					log.good("%s at %s, %d, bonus %d" % (sol_count[point], point, layer_map[point], world_map.bonus_map[point]))
					enemies = get_enemies(point, self._conn)
					log.good("enemies: %s" % enemies)
				elif click.button == 3:
					log.good('AAAAA')
					Clicker.target = point
				elif click.button == 5:
					log.good('swamp at %s' % point)
					world_map.set_swamp(point)
				print log.good("%s %s" % (click.button, type(click.button)))
			time.sleep(0.1)

def read_time():
	global round_no

	curr_round_no, turn_no, total_turns = conn.get_time()
	print 'round %d: %d/%d' % (curr_round_no, turn_no, total_turns)
	if curr_round_no > round_no:
		init_state()


def clustering(divisions):
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


def layerize(cluster, my_bonuses, good_bonuses):
	contention = (len(my_bonuses) == 3 and len(good_bonuses) == 3)
	def is_taken(point):
		if not contention: return sol_count[neigh]
		return sol_count[neigh] or world_map.bonus_map[neigh]
	
	que = collections.deque()
	for point in cluster:
		for neigh in point.neighs():
			if not world_map.is_swamp(neigh) and not is_taken(neigh):
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

def target_on_edge(bonus):
	for enemy in bonus:
		if sol_count[enemy]: continue
		for me in enemy.neighs():
			if sol_count[me]:
				return me
			
def recruit_find(divisions, clusters, my_bonuses, good_bonuses):
	target = Clicker.target
	if target is not None:
		Clicker.target = None
		return target
	
	to_conquer = my_bonuses.difference(good_bonuses)
	if 'spam' not in args.posargs and to_conquer and len(my_bonuses) <= 3:
		left_on_this_bonus = collections.defaultdict(int)
		for bonus_id in to_conquer:
			bonus = world_map.get_bonus(bonus_id)
			for point in bonus:
				if not sol_count[point]:
					left_on_this_bonus[bonus_id] += 1
		log.bad(left_on_this_bonus.items())
		bonus_id = min(left_on_this_bonus.keys(), key=lambda bid: left_on_this_bonus[bid]) 
		
#		bonus_id = list(to_conquer)[0]
		print 'conquering remaining %d!' % bonus_id
		return target_on_edge(world_map.bonuses[bonus_id-1])
	
	if 'spam' not in args.posargs and len(my_bonuses) < 3:
		avail_bids = set()
		for div in divisions:
			for neigh in div.point.neighs():
				bid = world_map.bonus_map[neigh]
				if bid and bid not in my_bonuses:
					avail_bids.add(bid)
		do_reverse = (len(good_bonuses) > 0)
		avail_bids = sorted(avail_bids, key=lambda bid: len(world_map.get_bonus(bid)), reverse=do_reverse)
		log.bad(map(lambda bid: (bid, len(world_map.get_bonus(bid))), avail_bids))
		if avail_bids:
			print 'conquering biggest!'
			for div in divisions:
				for neigh in div.point.neighs():
					if world_map.bonus_map[neigh] == avail_bids[0]:
						return div.point
	
	if 'boost' in args.posargs:
		return max(divisions, key=lambda div: div.n).point
	
	
	print 'fueling random...'
	edge = []
	for cluster in clusters:
		for point in cluster:
			if layer_map[point] == 1:
				for _ in xrange(len(cluster)):
					edge.append(point)
		
#	for point, layer in layer_map.iteritems():
#		if layer == 1:
#			edge.append(point)
	if edge:
		return random.Random().choice(edge)


def recruit(divisions, clusters, my_bonuses, good_bonuses):
	money = conn.money()
	print 'money: %d' % money

	point = recruit_find(divisions, clusters, my_bonuses, good_bonuses)
	if point is None: return
	try:
		print "recruiting %d at %s" % (money, point)
		conn.recruit_soldiers(point, money)
		sol_count[point] += money
	except connection.CommandFailedError as e:
		log.warn(e)
		
	worker.command(tid=1000, points=[tuple(point)], color=(255,255,0))
	

def choose_target(point, my_bonuses, good_bonuses, potential_bonuses):
	neighs = []
	for neigh in point.neighs():
		if not world_map.is_swamp(neigh):
			neighs.append(neigh)
	random.Random().shuffle(neighs)
	
	if len(my_bonuses) <= 3:
		for neigh in neighs:
			if world_map.bonus_map[neigh] in my_bonuses and not sol_count[neigh]:
				return neigh # defend!

		if len(my_bonuses) < 3:
			for neigh in neighs:
				if world_map.bonus_map[neigh] and not sol_count[neigh]:
					return neigh # attack!
		
		lower_neighs = []
		for neigh in neighs:
			if layer_map[neigh] < layer_map[point]:
				if len(good_bonuses) < 3:
					lower_neighs.append(neigh)
				else:
					if not world_map.bonus_map[neigh] or world_map.bonus_map[neigh] in good_bonuses:
						lower_neighs.append(neigh)
					
		if lower_neighs:
			if 'lskip' in args.posargs:
				return lower_neighs[0]
			for neigh in lower_neighs:
				if sol_count[neigh]: return neigh
			enemies_around = conn.get_field(point)
			for enemy in enemies_around.keys():
				if sol_count[enemy]:
					enemies_around[enemy] = 0
			for neigh in neighs:
				if neigh not in enemies_around.keys():
					world_map.set_swamp(neigh)
					enemies_around[neigh] = 10**9
			sorted_neighs = sorted(lower_neighs, key=lambda pt: enemies_around[pt])
			print "ATTACKING %d -> %d" % (sol_count[point], enemies_around[sorted_neighs[0]])
			if enemies_around[sorted_neighs[0]] > 0.5 * sol_count[point]:
				if len(sorted_neighs) > 1:
					log.good('withdrawal')
					return sorted_neighs[1]
				return None
			return sorted_neighs[0]
		
	else: # should never happen
		for neigh in neighs:
			if not world_map.bonus_map[neigh] and layer_map[neigh] < layer_map[point]:
				return neigh # leave all!
	return None
	
def attack(divisions):
	pass

def loop():
	global sol_count, layer_map, clusters
	read_time()
	old_cluster_len = len(clusters)
	
	# update sol_count
	divisions = conn.divisions()
	sol_count = collections.defaultdict(int)
	for div in divisions:
		sol_count[div.point] = div.n
	
	# compute clusters
	clusters = clustering(divisions)
	
	my_bonuses = world_map.my_bonuses()
	good_bonuses = world_map.good_bonuses()
	
	# layerize
	layer_map = collections.defaultdict(int)
	for cluster in clusters:
		layerize(cluster, my_bonuses, good_bonuses)
	
	recruit(divisions, clusters, my_bonuses, good_bonuses)
	
	# draw
	i = 0
	for i, cluster in enumerate(clusters):
		strength = 0
		points = []
		for point in cluster:
			strength += sol_count[point]
			points.append(tuple(point))
		worker.command(tid=i, points=points, label=str(strength))
	for j in xrange(i+1, old_cluster_len):
		worker.command(tid=j, action='remove')
		

	world_map.draw_swamps()
	world_map.draw_bonuses()
	
	# move
	orders_count = 0
	trials_count = 0
	permdiv = sorted(divisions, key=lambda div: div.n, reverse=True)
#	print permdiv[:5]
	potential_bonuses = set(my_bonuses)
	
	print map(lambda div: div.n, permdiv[:20])
	
	moves_from = []
	for div in permdiv:
		trials_count += 1
		if trials_count == 10: break
		if orders_count == 5: break
		if div.n == 1: break
		try:
			point = div.point	
			dest = choose_target(point, my_bonuses, good_bonuses, potential_bonuses)
			if dest is not None:
				if not sol_count[dest] and world_map.bonus_map[dest]: # conquering a bonus
					if world_map.bonus_map[dest] not in potential_bonuses:
						if len(potential_bonuses) >= 3:
							print "skipping bonus"
							continue
					potential_bonuses.add(world_map.bonus_map[dest])
				if sol_count[dest]:
					if not good_bonuses:
						strength = div.n
					else:
						strength = max(1, div.n - 5)
				elif world_map.bonus_map[dest]:
					strength = div.n
				else:
					if not good_bonuses:
						strength = div.n
					else:
						strength = int(div.n * 0.95)
				
				
				enemies = 0 #get_enemies(dest)
#				if strength < 20: continue
				
				if 'skip' in args.posargs:
					if strength < 10 and not sol_count[dest]:
						continue
					if strength < 30 and not sol_count[dest]:
						enemies = get_enemies(dest)
					if enemies is None:
						world_map.set_swamp(dest)
						continue
					if enemies > strength:
						print "skiping attack %d -> %d" % (strength, enemies)
						continue
				
				conn.move(point, dest, strength, 1)
				
				
				print "moving from", point, layer_map[point], "to", dest, layer_map[dest], "strength", strength, div.n, enemies
				moves_from.append(tuple(point))
				orders_count += 1
			else:
				log.bad('WAT? %s' % point)
		except connection.CommandFailedError as e:
			log.bad(e)
			if e.errno == 109:
				print dest, "is swamp"
				world_map.set_swamp(dest)
	
	worker.command(tid=700, points=moves_from, color=(255,255,255))
	
	print "my bonuses:", list(world_map.my_bonuses()), list(world_map.good_bonuses())
	
	war = map(tuple, conn.get_turn_result())
	worker.command(tid=-400, points=war, color=(30, 30, 30))
	
	

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
