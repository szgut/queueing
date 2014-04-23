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
	
	def readendur(self):
		endur = self.readstr()
		if endur != 'INF':
			endur = int(endur)
		return endur
	
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
	
	def list_owned_items(self):
		self.cmd('list_owned_items')
		ports, towers, artifacts = [], [], []
		n = self.readint()
		for _ in xrange(n):
			pos = Point(*self.readints(2))
			typ = self.readstr()
			endur = self.readendur()
			if typ.endswith('ARTIFACT'):
				artifacts.append(Ship(id=1, pos=pos, type=typ, endur=endur))
			elif typ == 'TOWER':
				towers.append(Field(pos=pos, type=typ, endur=endur, owner='ME'))
			else:
				ports.append(Field(pos=pos, type=typ, endur=endur, owner='ME'))
		return ports, towers, artifacts
			
	
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
		#print "move", ship_id
		self.throwing_cmd('move', ship_id, dx, dy)
		#print "moved", ship_id
	
	def shoot(self, ship_id, diff):
		self.cmd('shoot', ship_id, diff.x, diff.y)
		
	def launch_ship(self, ship_type='DESTROYER'):
		self.cmd('launch_ship', ship_type)
		return self.readints(3)[0]
	
	def myk(self, typ, ship_id, diff):
		self.cmd(typ, ship_id, diff.x, diff.y)
		

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
		self.islands = set()
		self.read_fields()
		
		self.artifacts = []
		
		self.fill_poses()
		
	def read_fields(self):
		#self.islands = set()
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
				
	def is_ok(self, pos):
		return not (pos.x < 1 or pos.x > self.N or pos.y < 1 or pos.y > self.N)
	
	def is_free(self, pos):
		if pos.x < 1 or pos.x > self.N or pos.y < 1 or pos.y > self.N:
			return False
		return pos not in self.fields_map and pos not in self.temp_map
	
	def fill_poses(self):
#		pos_now = {ship.id: ship.pos for ship in self.ships}
		self.poses = [{} for _ in xrange(10)]
	
	def ensure_pos(self, ship):
		if ship.id not in self.poses[0]:
			for pos in self.poses:
				pos[ship.id] = ship.pos
	
	def sweep_poses(self, ids):
		for pos in self.poses:
			for sid in pos.keys():
				if sid not in ids:
					del pos[sid]
					
	def erase_poses(self, sid):
		for pos in self.poses:
			if sid in pos:
				del pos[sid]
	
	def tick_poses(self):
		self.poses.pop(0)
		self.poses.append(dict(self.poses[-1]))
	
	def comp_mass_center(self):
		sm = Point(0.0, 0.0)
		for ship in self.ships:
			sm.x += ship.pos.x
			sm.y += ship.pos.y
		if self.ships:
			sm.x = int(round(sm.x/len(self.ships)))
			sm.y = int(round(sm.y/len(self.ships)))
		self.mass_center = sm
		
	
	def tick(self):
		self.tick_poses()
		
		self.temp_map = {}
		
		self.ships, self.enemies, self.artifacts = [], [], []
		for ship in conn.list_ships():
			self.temp_map[ship.pos] = ship
			self.ships.append(ship)
			self.ensure_pos(ship)
			#ship.tick()
		self.sweep_poses(set(map(lambda s: s.id, self.ships)))
		
		print map(lambda s: (s.id, s.pos), self.ships)[:7], '<<<'
		for pos in self.poses:
			print list(pos.iteritems())[:7]
		self.comp_mass_center()
		
		for target in conn.list_primary_targets():
			if target.type.endswith('ARTIFACT'):
				self.artifacts.append(target)
				#log.good(str(target))
				#spatrol_targets[-1] = target.pos
			else:
				self.temp_map[target.pos] = target
				self.enemies.append(target)
		ports, towers, artifacts = conn.list_owned_items()
		for port in ports:
			self.fields_map[port.pos] = port
			self.ports.add(port)
		for tower in towers:
			self.fields_map[tower.pos] = tower
			self.towers.add(tower)
		for artifact in artifacts:
			#self.temp_map[artifact.pos] = artifact
			self.artifacts.append(artifact)
			
		
	
	def draw_land(self):
		worker.command(tid=0, points=[tuple(island.pos) for island in self.islands],
					   color=Color.BROWN)
		for still in self.fields_map.itervalues():
			if still.type != 'ISLAND':
				still.draw()
#		for tid, port in enumerate(self.ports, 1000):
#			worker.command(tid=tid, points=[tuple(port.pos)], label=str(port.endur),
#					   	   color=Color.LIGHT_BLUE)
#		for tid, tower in enumerate(self.towers, 2000):
#			worker.command(tid=tid, points=[tuple(tower.pos)], label=str(tower.endur),
#							color=Color.GRAY)
		for artifact in self.artifacts:
			artifact.draw()
		for moveable in self.temp_map.itervalues():
			moveable.draw()
		try:
			if patrol_targets.get(-1, None) is not None:
				worker.command(tid=-1, points=[tuple(patrol_targets[-1])], color=Color.WHITE)
		except KeyError:
			pass

		

class Point(gui.Point):
	
	def neighs(self):
		yield Point(self.x, self.y+1)
		yield Point(self.x, self.y-1)
		yield Point(self.x-1, self.y)
		yield Point(self.x+1, self.y)
		yield Point(self.x+1, self.y+1)
		yield Point(self.x+1, self.y-1)
		yield Point(self.x-1, self.y+1)
		yield Point(self.x-1, self.y-1)

	def dist(self, point):
		return self.shoot_dist(point)
	
	def diff(self, point):
		return Point(point.x - self.x, point.y - self.y)
	
	def shoot_dist(self, point):
		return max(abs(self.x - point.x), abs(self.y - point.y))


class Ship(slottedstruct.SlottedStruct):
	__slots__ = ('id', 'pos', 'type', 'endur', 'turns_left')
	
	#def __repr__(self):
	#	return "%s\t(%d, %d)\t%s\t%s" % (self.id, self.pos.x, self.pos.y, self.type, self.endur)
	def __repr__(self):
		return "%s %s %s %s %s %s %s" % (self.type, self.owner, self.pos, self.endur, self.id,
									str(self.at()) if self.is_artifact() else "", self.turns_left) 
	
#	@property
#	def future_pos(self):
#		return world_map.future_pos[]
#	
#	def future_pos(self, t):
#		return 
#	
	@property
	def owner(self):
		return 'ME' if self.is_mine() else 'ENEMY'
	
	def color(self):
		#return {'CRUISER': Color.MAGENTA, 'DESTROYER': Color.RED, 'PATROL': Color.PINK}[self.type]
		if self.is_artifact(): return Color.PINK
		if self.is_mine(): return Color.GREEN
		return Color.RED
	
	def label(self):
		if self.is_artifact():
			return self.type[:1]# + ("-my" if  
		return "%d%s" % (self.endur, self.type[:1])
	
	def draw(self):
		worker.command(tid=(self.is_artifact(), hash(self)), points=[tuple(self.pos)], label=self.label(), color=self.color())
	
	def is_mine(self):
		return self.id is not None
	
	def is_artifact(self):
		return self.type.endswith('ARTIFACT')
	
	def at(self):
		return world_map.fields_map.get(self.pos, None) or world_map.temp_map.get(self.pos, None)
	
	
	
	def futures(self):
		return map(lambda di: di[self.id], world_map.poses)
	
	@property
	def inertia(self):
		return {'CRUISER': 6, 'DESTROYER': 2, 'PATROL': 1}[self.type]
	
	
	
	def target(self):
		#other_art = filter(lambda art: art.owner!='ME', world_map.artifacts)
		if self.turns_left != 'NA':
			return None
		
		my = self.my_artifact()
		secured = filter(lambda a: a.owner=='ME' and a.type.startswith('SEC'), world_map.artifacts)
		if my and secured:
			closest = min(secured, key=lambda a: self.pos.dist(a.pos))
			#print self, "going to", closest
			if self.pos.dist(closest.pos) == 1:
				try:
					conn.myk('put', self.id, self.pos.diff(closest.pos))
				except connection.CommandFailedError:
					pass
				return None
			return closest.pos
		if my:
			return world_map.mass_center
		
		
		secpts = set(map(lambda a: a.pos, filter(lambda a: a.owner=='ME' and a.type.startswith('SEC'), world_map.artifacts)))
		getpts = set(map(lambda a: a.pos, filter(lambda a: a.owner=='ME' and a.type.startswith('GET'), world_map.artifacts)))
		both = secpts.intersection(getpts)
		joiners = filter(lambda s: s.turns_left!='NA', world_map.ships)
		def jdist(pos):
			j = min(joiners, key=lambda j: j.pos.dist(pos))
			return j.pos.dist(pos)
		if joiners:
			both = [pos for pos in both if jdist(pos) > 1]
		
		if both:
			print "BOTH", both
			p = min(both, key=lambda p: self.pos.dist(p))
			if self.pos.dist(p) == 1:
				try:
					conn.myk('join', self.id, self.pos.diff(p))
				except connection.CommandFailedError as e:
					log.bad(e)
			return p
			
		
		aim = patrol_targets.get(-1, None)
		if aim:
			#print "aim"
			return aim
		
		#print map(lambda art: art.owner, world_map.artifacts)
		towers = filter(lambda t: t.owner!='ME', world_map.towers)
		if not towers:
			#print "mass"
			#if 'mass' in args.posargs:
			diff = world_map.mass_center.diff(self.pos)
			return Point(self.pos.x+diff.x, self.pos.y+diff.y)
			#return patrol_targets.get(-1, None)
		else:
			#print "tower"
			return min(towers, key=lambda t: self.pos.dist(t.pos)).pos
	
	def my_artifact(self):
		for artifact in world_map.artifacts:
			if artifact.pos == self.pos:
				return artifact
		return None
	
	def _get_new_target(self):
		N = world_map.N
		patrol_targets[-1] = Point(random.randint(1,N), random.randint(1,N))
		#patrol_targets[self.id] = Point(random.randint(1,N), random.randint(1,N))

	
	def patrol(self):
		target = self.target()
		if target is None:
			return
		
		time = self.inertia
		mypos = world_map.poses[time][self.id]
		dist = mypos.dist(target)
		diff = mypos.diff(target)
		def key(neigh):
			ndiff = mypos.diff(neigh)
			return ndiff.x*diff.x + ndiff.y*diff.y
		for neigh in sorted(mypos.neighs(), key=key, reverse=True):
			if world_map.is_ok(neigh) and neigh.dist(target)<dist and neigh not in world_map.fields_map and neigh not in world_map.poses[time+1].values():
			#if world_map.is_free(neigh) and neigh.dist(target) < dist:
				#if 
				
				#print "moving", self.pos, neigh
				move = mypos.diff(neigh)
				try:
					conn.move(self.id, move.x, move.y)
					#del world_map.temp_map[self.pos]
					#self.pos = neigh
					for pos in world_map.poses[time+1:]:
						pos[self.id] = neigh
				except connection.CommandFailedError as e:
					log.bad(str(e))
					if isinstance(e, connection.ForcedWaitingError):
						raise
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
		shoots = min(max(0, ammo), enemy.endur + (5 if enemy.type == 'TOWER' else 0))
		done = 0
		try:
			for _ in xrange(shoots):
				conn.shoot(self.id, self.pos.diff(enemy.pos))
				print "shooting to", enemy
				if enemy.type != 'TOWER':
					enemy.endur -= 1
				done += 1
		except connection.CommandFailedError as e:
			log.bad(str(e))
		return done
	
	def try_to_shoot(self):
		try:
			seen = filter(lambda enemy: self.in_shoot_range(enemy.pos), world_map.enemies)
			seens = sorted(seen, key=lambda enemy: enemy.in_shoot_range(self.pos), reverse=True)
			ammo = self.shoot_ammo
			for enemy in seens:
				if not ammo: break
				ammo -= self.shoot(enemy, ammo)
			
#			for artifact in filter(lambda artifact: artifact.owner != 'ME', world_map.artifacts):
#				if self.in_shoot_range(artifact.pos):
#					ammo -= self.shoot(artifact.tower, ammo)
				
			ports = filter(lambda port: port.owner!='ME' and self.in_shoot_range(port.pos), world_map.ports)
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

	def color(self):
		if self.type == 'ISLAND': return Color.BROWN
		if self.type == 'PORT': return Color.LIGHT_BLUE
		return Color.GRAY
	
	def label(self):
		return str(self.endur) + ("*" if self.owner == 'ME' else "?")

	def draw(self):
		worker.command(tid=hash(self), points=[tuple(self.pos)], label=self.label(), color=self.color())


class Clicker(gui.Clicker):
	def __call__(self, click):
		print "CLICK", click.point, click.button
		if click.button == 3:
			if patrol_targets.get(-1, None) is not None:
				patrol_targets[-1] = None
			else:
				patrol_targets[-1] = click.point
		elif click.button == 2:
			sh = world_map.temp_map.get(Point(*click.point), None)
			if sh is not None and sh.is_mine() and not sh.is_artifact():
				if sh.turns_left != 'NA':
					conn.cmd('use_key', sh.id)
				else:
					print "soraski"
		elif click.button == 1:
			print world_map.fields_map.get(Point(*click.point), None)
			print world_map.temp_map.get(Point(*click.point), None)
			sh = world_map.temp_map.get(Point(*click.point), None)
			if sh is not None and sh.is_mine() and not sh.is_artifact():
				print sh.futures()


def build_ships():
	money = conn.my_stat()[0]
	try:
		for _ in xrange(money):
			if 'light' in args.posargs:
				shipid = conn.launch_ship('DESTROYER')
			else:
				shipid = conn.launch_ship('CRUISER')
			world_map.erase_poses(shipid)
			log.good('ship built')
	except connection.CommandFailedError as e:
		log.bad(e)

def take_gettable():
	gettables = filter(lambda a: a.type.startswith('GET'), world_map.artifacts)
	#print gettables
	#print world_map.ships
	for gettable in gettables:
		at = gettable.at()
		#if at is not None or at.type != 'TOWER' or :
		#	continu
		secs = filter(lambda a: a.type.startswith('SEC') and a.pos==gettable.pos, world_map.artifacts)
		ok = not secs and (at is None or (at is not None and at.type == 'TOWER' and at.owner == 'ME'))
		if not ok: continue
		for ship in world_map.ships:
			if ship.pos.dist(gettable.pos) == 1:
				if 'notake' not in args.posargs:
					try:
						conn.myk('GET', ship.id, ship.pos.diff(gettable.pos))
					except connection.CommandFailedError as e:
						log.bad(e)
				log.good('taken')
				break
				
def move_cargo():
	for ship in world_map.ships:
		if ship.my_artifact() is not None:
			log.good("cargo %s" % ship)
			ship.patrol()


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
	
	if 'nobuild' not in args.posargs:
		build_ships()
	
	world_map.read_fields()
	world_map.tick()
	print "artifacts:"
	for artifact in world_map.artifacts:
		print artifact
	print "towers:"
	for tower in world_map.towers:
		print tower
	print "ports:"
	for port in world_map.ports:
		print port
	
	worker.command(action='clear')
	world_map.draw_land()
	take_gettable()
	move_cargo()
	for ship in world_map.ships:
		ship.try_to_shoot()
	if 'stay' not in args.posargs:
		for ship in world_map.ships:
			ship.patrol()
#	if 'light' in args.posargs:
#		for ship in world_map.ships:
#			if ship.type == 'PATROL':
#				ship.patrol()
	for enemy in world_map.enemies:
		print enemy
	
	print "========="
	print conn.time_to_full_moon()
	print conn.my_stat(), world_map.N


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
			try:
				loop()
			except connection.ForcedWaitingError:
				print "skipping wait"
				#conn.wait()
			else:
				conn.wait()
	except KeyboardInterrupt:
		serializer.save((world_map, round_no))
		pass
	except:
		traceback.print_exc()
		serializer.save((world_map, round_no), ".crash")
