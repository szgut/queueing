#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import traceback
import time

from dl24 import connection
from dl24 import log
from dl24.log import color, BLUE, GREEN, RED
from dl24 import misc
from dl24 import slottedstruct

from gui import Gui

class Config(object):
	def __init__(self, universum=1):
		self.host = '10.120.8.13'
		self.datafile = 'wat-data%i' % universum
		self.port = 7031+universum-1

class Field(slottedstruct.SlottedStruct):
	__slots__ = ('t', 'r', 'team', 'water', 'kind', 'upd')

class Connection(connection.Connection):
	def __init__(self, *args, **kwargs):
		super(Connection, self).__init__(*args, **kwargs)
		self.upd_time_info()
		self.describe_world()
		self.update_sources()
		self.my_contracts = []
		self.money = 0
		self.is_waiting = False
		self.is_sleeping = False

	# implementacja komend z zadania
	def get_building_result(self):
		self.cmd("GET_BUILDING_RESULT")
		n, = self.readints(1)
		for i in range(0, n):
			res = self.readints(7)
			res.append(self.readstr())
			yield res

	def get_my_money(self):
		self.cmd("GET_MY_MONEY")
		money, = self.readints(1)
		return money

	def describe_world(self):
		self.cmd("DESCRIBE_WORLD")
		self.n, self.id, self.max_debt = self.readints(3)
		self.w1, self.w2, self.w3, self.w4 = self.readints(4)
		# returns nothing!

	def show_map(self, x, y, m):
		self.cmd("SHOW_MAP", x, y, m)
		h = {}
		for _x in range(0, 5):
			for _y in range(0, 5):
				t, r, team = self.readints(3)
				w, k = self.readstr(), self.readstr()
				f = Field(t, r, team, w, k, upd=self.turn)
				h[x+_x, y+_y] = f
		return h

	def update_map(self, max_cmd = 15):
		for i in range(0, max_cmd):
			x, y = self.where_update_map(gs.m, 5)
			if x == 0 and y == 0:
				return
			gs.m.update(self.show_map(x, y, 5))

	def upd_time_info(self):
		self.cmd("GET_TIME")
		self.r, self.turn, self.T = self.readints(3)

	# returns where to update map info (where the sum of
	# field ages is the greatest for a 5x5 map part
	def where_update_map(self, m, patch_size):
		best = 0, 0
		bscore = 0
		t = time.time()
		scores = []
		for y in range(1, self.n+1):
			line = []
			for x in range(1, self.n+1):
				if (x, y) not in m:
					line.append(self.turn)
				else:
					elem = m[x, y]
					line.append(self.turn - elem.upd)
			scores.append(line)
		for x in range(1, self.n+1-patch_size):
			for y in range(1, self.n+1-patch_size):
				score = 0
				for _x in range(x, x+patch_size):
					for _y in range(y, y+patch_size):
						score += scores[_y][_x]
				if score > bscore:
					best = x, y
					bscore = score

		print time.time() - t
		#cols = [0]*(n-patch_size)
		#for x in range (1, self.n+1):
		#	for y in range(1, 6):

		#for y in range(1, self.n+1-patch_size):
		#	for x in range(1, self.n+1):
		#		cols[x] += scores[y][x]
		#	score = 0
		#	for x in range(1, 6):
		#		score += cols[x]
		return best

	def update_contracts(self):
		self.cmd("GET_OFFERED_CONTRACTS")
		k, = self.readints(1)
		self.contracts = {}
		for i in range(0, k):
			x, y, idd = self.readints(3)
			self.contracts[x, y] = idd
		self.cmd("GET_MY_CONTRACTS")
		k, = self.readints(1)
		self.my_contracts = {}
		for i in range(0, k):
			x, y, idd = self.readints(3)
			self.my_contracts[x, y] = idd

	def build(self, x, y, t, r, a):
		try:
			self.cmd("BUILD", x, y, t, r, a)
		except:
			pass

	def acc_contract(self, i, a):
		self.cmd("ACCEPT_CONTRACT", i, a)

	def drop_contract(self, idd, x, y):
		self.cmd("GIVE_UP_CONTRACT", idd)
		del self.my_contracts[x, y]

	def get_store(self):
		self.cmd("GET_STORE")
		nums = self.readints(6)
		store = {}
		for i, a in enumerate(nums):
			store[i+1] = a
		return store

	def update_my_pipes(self):
		self.cmd("GET_MY_PIPES")
		nums = self.readints(6)
		self.pipes = {}
		for i, a in enumerate(nums):
			self.pipes[i+1] = a

	def buy_pipe(self, t, a):
		self.cmd("BUY_PIPE", t, a)

	def update_sources(self):
		self.cmd("GET_SOURCES")
		k, = self.readints(1)
		self.sources = {}
		for i in range(0, k):
			x, y, rot = self.readints(3)
			self.sources[x, y] = rot
	def wait_lock(self):
		self.is_waiting = True
		self.wait()
		self.started_at = time.time()
		self.is_waiting = False



def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-d", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	parser.add_argument('posargs', nargs='?', default=[])
	return parser.parse_args()


class PersistentState(object):
	def __init__(self):
		self.a = 0


def init_state(read):
	global gs
	if read:
		gs = serializer.load()
	else:
		gs = PersistentState()
		gs.m = {}

def check_last_build_actions(conn):
	actions = list(conn.get_building_result())
	for a in actions:
		x, y = a[3:5]
		if (x, y) in gs.m:
			# update next time, please
			gs.m[x, y].upd = -100000
			gs.m[x, y].team = a[0]
			gs.m[x, y].t = a[5]
			gs.m[x, y].r = a[6]
			gs.m[x, y].kind = 'S'
		else:
			gs.m[x, y] = Field(a[5], a[6], a[0], 'N', 'S', upd=-10000)
	log.info("updated %i actions" % len(actions))


def loop():
	check_last_build_actions(conn)
	conn.update_contracts()
	store = conn.get_store()
	conn.update_my_pipes()
	for (x, y), cid in conn.contracts.items():
		if (x, y) in gs.m:
			gs.m[x, y].upd = -100000
		else:
			gs.m[x, y] = Field(7, 0, 0, 'N', 'S', upd=-10000)
	conn.update_map(5)
	if len(conn.my_contracts) < 2:
		contract_ids = conn.contracts.values()
		conn.acc_contract(contract_ids[0], 20)

	# buying pipes
	if conn.turn % 5 == 1:
		for pipe, num in conn.pipes.items():
			if num < 4 and store[pipe] != 0:
				conn.buy_pipe(pipe, 10)

	if conn.turn % 5 == 0:
		conn.money = conn.get_my_money()

def on_build(x, y, button, tool, rot):
	while not conn.is_sleeping:
		time.sleep(0.05)
	if (x, y) in gs.m:
		gs.m[x, y].upd = -100000
	else:
		gs.m[x, y] = Field(0, 0, 0, 0, 0, upd=-100000)
	if button == 2 and (x, y) in conn.my_contracts:
		conn.drop_contract(conn.my_contracts[x, y], x, y)
	elif button == 1:
		conn.build(x, y, tool, rot, 10)

if __name__ == '__main__':
	args = parse_args()
	print args.posargs
	config = Config(args.universum)
	serializer = misc.Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	if args.universum == 1:
		conn.rtime = 5
	else:
		conn.rtime = 1
	log.info("logged in")

	init_state(args.loadstate)
	gs.a += 1
	print gs.a

	iteration = 0

	try: # main loop
		gui = Gui(args.universum, on_build)
		# just in case, wait for the next turn to start
		conn.wait_lock()

		tool = 0
		rot = 0
		while 1:
			loop()
			log.info("")
			log.info(color(BLUE, '[r:%i %i/%i m:%i]-------' % (conn.r, conn.turn, conn.T, conn.money)))
			log.info(color(BLUE, 'w = %i %i %i %i' % (conn.w1, conn.w2, conn.w3, conn.w4)))
			gui.update_viz(gs.m, conn)
			remaining = conn.rtime - (time.time() - conn.started_at)
			conn.is_sleeping = True
			if (remaining - 0.05 > 0):
				time.sleep(remaining - 0.05)
			conn.is_sleeping = False
			conn.wait_lock()
			conn.turn += 1
			if conn.turn >= conn.T:
				break;
		log.info("End of round")
		if iteration % 30 == 29:
			serializer.save(gs)
			log.info("extra save!")
		iteration += 1
	except KeyboardInterrupt:
		gui.stop()
		serializer.save(gs)
	except:
		gui.stop()
		traceback.print_exc()
		serializer.save(gs, ".crash")
