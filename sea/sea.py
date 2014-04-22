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
	
	def my_stat(self):
		self.cmd('my_stat')
		return self.readline()
	
	def move(self, ship_id, dx, dy):
		self.cmd('move', ship_id, dx, dy)
		

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-d", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	parser.add_argument('posargs', nargs='*', default=[])
	return parser.parse_args()



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

class WorldMap(object):
	
	def __init__(self, N, A):
		self.N = N
		self.A = A
		self.read_fields()
		self.read_ships()
		
	def read_fields(self):
		self.islands = set()
		self.ports = set()
		self.fields_map = {}
		for field in conn.list_lands_nearby():
			self.fields[field.pos] = field
			if field.type == 'ISLAND':
				self.islands.add(field)
			if field.type == 'PORT':
				self.ports.add(field)
			
	def read_ships(self):
		self.ships_map = {}
		for ship in conn.list_ships():
			self.ships_map[ship.id] = ship
	
	@property
	def ships(self):
		return self.ships_map.itervalues()
	
	def is_free(self, pos):
		if pos.x < 1 or pos.x > self.N or pos.y < 1 or pos.y > self.N:
			return False
		return pos not in self.fields_map

	def draw_land(self):
		worker.command(tid=0, points=[tuple(island.pos) for island in self.islands],
					   color=Color.BROWN)
		for tid, port in enumerate(self.ports, 10000):
			worker.command(tid=tid, points=[tuple(port.pos)], label=str(port.endur),
					   	   color=Color.LIGHT_BLUE)
		


class Ship(slottedstruct.SlottedStruct):
	__slots__ = ('id', 'pos', 'type', 'endur', 'turns_left', 'target')
	
	def color(self):
		return {'CRUISER': Color.MAGENTA, 'DESTROYER': Color.RED, 'PATROL': Color.PINK}[self.type]
	
	def draw(self):
		worker.command(tid=100+self.id, points=[tuple(self.pos)],
					   label=str(self.endur), color=self.color())
	
	def _get_new_target(self):
		N = world_map.N
		self.target = Point(random.randint(1,N), random.randint(1,N))
	
	def patrol(self):
		if self.target is None or self.pos == self.target:
			self._get_new_target()
		dist = self.pos.dist(self.target)
		for neigh in self.pos.neighs():
			if world_map.is_free(neigh) and neigh.dist(self.target) < dist:
				print "moving", self.pos, neigh
				move = self.pos.diff(neigh)
				conn.move(self.id, move.x, move.y)
				break
		
	

class Field(slottedstruct.SlottedStruct):
	__slots__ = ('pos', 'type', 'owner', 'endur')


def init_state(read=False):
	global world_map
	if read:
		world_map = serializer.load()
	else:
		N, A, _, _ = conn.describe_world()
		world_map = WorldMap(N, A)


def loop():
	world_map.draw_land()
	for ship in world_map.ships():
		ship.draw()
		ship.patrol()
	
	print conn.my_stat()


if __name__ == '__main__':
	args = parse_args()
	print args.posargs
	config = Config(args.universum)
	serializer = misc.Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	log.info("logged in")

	worker = gui.Worker(title='SEA-%d' % args.universum)
	init_state(args.loadstate)
	#gs.a += 1
	#print gs.a
	
	try: # main loop
		while 1:
			loop()
			conn.wait()
	except KeyboardInterrupt:
		serializer.save(world_map)
		pass
	except:
		traceback.print_exc()
		serializer.save(world_map, ".crash")
