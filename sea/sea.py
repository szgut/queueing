#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import random
import traceback

from dl24 import connection
from dl24 import log
from dl24 import misc
from dl24 import slottedstruct
from dl24 import gui
from dl24.gui import Color



class Config(object):
	def __init__(self, universum=1):
		self.host = 'universum.dl24'
		self.datafile = 'data'
		self.port = 20003+universum-1


class Connection(connection.Connection):
	def describe_world(self):
		self.cmd('describe_world')
		return self.readint(), self.readint(), self.readint(), self.readfloat()
	
	def list_ships(self):
		self.cmd('list_ships')
		n = self.readint()
		ships = []
		for _ in xrange(n):
			ship = Ship()
			ship.id = self.readint()
			ship.pos = Point(*self.readints(2))
			ship.type = self.readstr()
			ship.endur = self.readint()
			ship.turns_left = self.readstr()
			ships.append(ship)
		return ships
	
	def list_lands_nearby(self):
		self.cmd('list_lands_nearby')
		n = self.readint()
		fields = []
		for _ in xrange(n):
			field = Field()
			field.pos = Point(*self.readints(2))
			field.type = self.readstr()
			field.owner = self.readstr()
			field.endur = self.readstr()
			if field.endur != 'INF':
				field.endur = int(field.endur)
			fields.append(field)
		return fields
	
	def list_primary_targets(self):
		self.cmd('list_primary_targets')
		n = self.readint()
		ships = []
		for _ in xrange(n):
			ship = Ship(pos=Point(*self.readints(2)), type=self.readstr(), endur=self.readstr())
			if ship.endur != 'INF':
				ship.endur = int(ship.endur)
			ships.append(ship)
		return ships
	
	def my_stat_str(self):
		self.cmd('my_stat')
		return self.readline()

	def my_stat(self):
		self.cmd('my_stat')
		return self.readint(), self.readint(), self.readstr(), self.readint(), self.readint(), self.readint(), self.readfloat()
	
	def time_to_full_moon(self):
		self.cmd('time_to_full_moon')
		status = self.readstr()
		M, L, P = self.readints(3)
		towers = [Point(*self.readints(2)) for _ in xrange(P)]
		return status, M, L, towers
	
	def round_no(self):
		return self.time_to_full_moon()[2]
	
	def move(self, ship_id, dx, dy):
		self.cmd('move', ship_id, dx, dy)
	
	def shoot(self, ship_id, diff):
		self.cmd('shoot', ship_id, diff.x, diff.y)
		
	def launch_ship(self, ship_type='DESTROYER'):
		self.cmd('launch_ship', ship_type)
		return self.readints(3)
		

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-d", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	parser.add_argument('posargs', nargs='*', default=[])
	return parser.parse_args()



class WorldMap(object):
	
	def __init__(self, N, A):
		self.N = N
		self.A = A

		self.fields_map = {}
		self.read_fields()
		
		self.artifacts = []
		
	def read_fields(self):
		self.islands = set()
		self.ports = set()
		self.towers = set()
		for field in conn.list_lands_nearby():
			self.fields_map[field.pos] = field
			if field.type == 'ISLAND':
				self.islands.add(field)
			if field.type == 'PORT':
				self.ports.add(field)
			if field.type == 'TOWER':
				self.towers.add(field)
			
	def is_free(self, pos):
		if pos.x < 1 or pos.x > self.N or pos.y < 1 or pos.y > self.N:
			return False
		return pos not in self.fields_map and pos not in self.temp_map
	
	def read_enemies_artifacts(self):
		self.enemies, self.artifacts = [], []
		
	
	def tick(self):
		self.temp_map = {}
		self.ships, self.enemies, self.artifacts = [], [], []
		for ship in conn.list_ships():
			self.temp_map[ship.pos] = ship
			self.ships.append(ship)
		for target in conn.list_primary_targets():
			self.temp_map[target.pos] = target
			if target.type.endswith('ARTIFACT'):
				self.artifacts.append(target)
				log.good(str(target))
				print target.tower
			else:
				self.enemies.append(target)
		
	
	def draw_land(self):
		worker.command(tid=0, points=[tuple(island.pos) for island in self.islands],
					   color=Color.BROWN)
		for tid, port in enumerate(self.ports, 1000):
			worker.command(tid=tid, points=[tuple(port.pos)], label=str(port.endur),
					   	   color=Color.LIGHT_BLUE)
		for tid, tower in enumerate(self.towers, 2000):
			worker.command(tid=tid, points=[tuple(tower.pos)], label=str(tower.endur),
							color=Color.GRAY)
		for moveable in self.temp_map.values():
			moveable.draw()
		

class Point(gui.Point):
	
	def neighs(self):
		yield Point(self.x, self.y+1)
		yield Point(self.x, self.y-1)
		yield Point(self.x-1, self.y)
		yield Point(self.x+1, self.y)

	def dist(self, point):
		return abs(self.x - point.x) + abs(self.y - point.y)
	
	def diff(self, point):
		return Point(point.x - self.x, point.y - self.y)
	
	def shoot_dist(self, point):
		return max(abs(self.x - point.x), abs(self.y - point.y))


class Ship(slottedstruct.SlottedStruct):
	__slots__ = ('id', 'pos', 'type', 'endur', 'turns_left')
	
	def __repr__(self):
		return "%s\t(%d, %d)\t%s\t%s" % (self.id, self.pos.x, self.pos.y, self.type, self.endur)
	
	def color(self):
		#return {'CRUISER': Color.MAGENTA, 'DESTROYER': Color.RED, 'PATROL': Color.PINK}[self.type]
		if self.is_mine(): return Color.GREEN
		if self.is_artifact(): return Color.PINK
		return Color.RED
	
	def label(self):
		if self.is_artifact(): return self.type[:1]
		return "%d%s" % (self.endur, self.type[:1])
	
	def tid(self):
		if self.id is not None: return 100+self.id
		else: return hash(self)
	
	def draw(self):
		worker.command(tid=self.tid(), points=[tuple(self.pos)], label=self.label(), color=self.color())
	
	def is_mine(self):
		return self.id is not None
	
	def is_artifact(self):
		return self.type.endswith('ARTIFACT')
	
	@property
	def tower(self):
		return world_map.fields_map[self.pos]
		
	
	
	@property
	def target(self):
		if not world_map.artifacts:
			return patrol_targets.get(-1, None)
		else:
			return world_map.artifacts[0].pos
	
	
	
	def _get_new_target(self):
		N = world_map.N
		patrol_targets[-1] = Point(random.randint(1,N), random.randint(1,N))
		#patrol_targets[self.id] = Point(random.randint(1,N), random.randint(1,N))

	
	def patrol(self):
		if self.target is None or self.pos == self.target:
			self._get_new_target()
		dist = self.pos.dist(self.target)
		diff = self.pos.diff(self.target)
		def key(neigh):
			ndiff = self.pos.diff(neigh)
			return ndiff.x*diff.x + ndiff.y*diff.y
		for neigh in sorted(self.pos.neighs(), key=key, reverse=True):
			if world_map.is_free(neigh) and neigh.dist(self.target) < dist:
				#print "moving", self.pos, neigh
				move = self.pos.diff(neigh)
				conn.move(self.id, move.x, move.y)
				break
	
	RANGE_LB = {'CRUISER': 3, 'DESTROYER': 1, 'PATROL': 1}
	RANGE_UB = {'CRUISER': 7, 'DESTROYER': 3, 'PATROL': 2} 
	def in_shoot_range(self, point):
		lb, ub = self.RANGE_LB[self.type], self.RANGE_UB[self.type]
		return lb <= self.pos.shoot_dist(point) <= ub
	
	@property
	def shoot_ammo(self):
		return {'CRUISER': 2, 'DESTROYER': 4, 'PATROL': 1}[self.type]
	
	def shoot(self, enemy, ammo):
		shoots = min(max(0, ammo), enemy.endur)
		for _ in xrange(shoots):
			print "shooting to", enemy
			conn.shoot(self.id, self.pos.diff(enemy.pos))
			enemy.endur -= 1
		return shoots
	
	def try_to_shoot(self):
		try:
			seen = filter(lambda enemy: self.in_shoot_range(enemy.pos), world_map.enemies)
			seens = sorted(seen, key=lambda enemy: enemy.in_shoot_range(self.pos), reverse=True)
			ammo = self.shoot_ammo
			for enemy in seens:
				if not ammo: break
				ammo -= self.shoot(enemy, ammo)
			
			for artifact in world_map.artifacts:
				if self.in_shoot_range(artifact.pos):
					ammo -= self.shoot(artifact.tower, ammo)
				
			ports = filter(lambda port: port.owner=='ENEMY' and self.in_shoot_range(port.pos), world_map.ports)
			if ports:
				ammo -= self.shoot(ports[0], ammo)
			
			towers = filter(lambda tower: tower.owner!='ME' and self.in_shoot_range(tower.pos), world_map.towers)
			if towers:
				ammo -= self.shoot(towers[0], ammo)
			
		except connection.CommandFailedError as e:
			log.bad(e)
		
	

class Field(slottedstruct.SlottedStruct):
	__slots__ = ('pos', 'type', 'owner', 'endur')

	def __repr__(self):
		return "%s %s %s %s" % (self.type, self.owner, self.pos, self.endur)

class Clicker(gui.Clicker):
	def __call__(self, click):
		if click.button == 3:
			print "CLICK", click.point
			patrol_targets[-1] = click.point 


def build_ships():
	money = conn.my_stat()[0]
	for _ in xrange(money):
		try:
			conn.launch_ship()
			log.good('ship built')
		except connection.CommandFailedError as e:
			log.warn(e)
			


def init_state(read=False):
	global world_map, round_no, patrol_targets
	if read:
		world_map, round_no = serializer.load()
	else:
		N, A, _, _ = conn.describe_world()
		world_map = WorldMap(N, A)
		round_no = conn.round_no()
	patrol_targets = {}


def read_time():
	global round_no
	old_round_no = round_no
	round_no = conn.round_no()
	if round_no > old_round_no:
		init_state()

def loop():
	read_time()
	log.info("round %d" % round_no)
	
	build_ships()
	
	world_map.read_fields()
	world_map.tick()
	worker.command(action='clear')
	world_map.draw_land()
	for ship in world_map.ships:
		print ship
		ship.draw()
		ship.try_to_shoot()
	if 'stay' not in args.posargs:
		for ship in world_map.ships:
			ship.patrol()
	for enemy in world_map.enemies:
		print enemy
	
	print conn.time_to_full_moon()
	print conn.my_stat()


if __name__ == '__main__':
	args = parse_args()
	print args.posargs
	config = Config(args.universum)
	serializer = misc.Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	log.info("logged in")

	worker = gui.Worker(title='SEA-%d' % args.universum, clicker=Clicker())
	init_state(args.loadstate)
	#gs.a += 1
	#print gs.a
	
	try: # main loop
		while 1:
			loop()
			conn.wait()
	except KeyboardInterrupt:
		serializer.save((world_map, round_no))
		pass
	except:
		traceback.print_exc()
		serializer.save((world_map, round_no), ".crash")
