#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import dl24.connection
from dl24.misc import Serializer
from dl24.misc import delay_sigint
from dl24.colors import warn, bad, good, info
import argparse
import traceback

def flatten(l):
	return sum(l, [])

class Config(object):
	def __init__(self, universum=1):
		self.host = 'universum.dl24'
		self.datafile = 'data' + str(universum)
		self.port = 20000+universum-1

def print_ar(arr):
	for a in arr:
		print(a)

def print_sq(s):
	for l in s:
		st = []
		for i in l:
			if i is None:
				st += '.'
			else:
				st += repr(i)
		print(' '.join(st))

class Beetle(object):
	def __init__(self, n):
		self.closest = None
		self.n = n
		self.state = {}
		self.state['act'] = 'idle'
		self.state['route'] = [0, 0]
		pass

	def __repr__(self):
		l1 = ("B%i(%i, %i)\tst:%i busy:%i %s close: %s rt:%s" %
			(self.n, self.x, self.y, self.sticks, self.busy, self.role, self.closest, self.state['route']))
		l2 = repr(self.state)
		return '\n'.join([l1, l2])

	def f(self):
		ar = [
				[None, None, None],
				[None, None, None],
				[None, None, None]
		]
		for j in range(-1, 2):
			for i in range(-1, 2):
				try:
					ar[j+1][i+1] = self.fields[j, i]
				except KeyError:
					pass
		return ar

	def step(self, conn):
		if self.state['route'][0] > 0:
			conn.move(self.n, 1, 0)
			self.state['route'][0] -= 1
		elif self.state['route'][0] < 0:
			conn.move(self.n, -1, 0)
			self.state['route'][0] += 1
		elif self.state['route'][1] > 0:
			conn.move(self.n, 0, 1)
			self.state['route'][1] -= 1
		elif self.state['route'][1] < 0:
			conn.move(self.n, 0, -1)
			self.state['route'][1] += 1

	@property
	def my_field(self):
		return self.fields[0, 0]



class Map(object):
	def __init__(self, dim):
		self.dim = dim
		self.m = []
		for j in range(0, self.dim):
			line = []
			for i in range(0, self.dim):
				line.append(None)
			self.m.append(line)

	def __getitem__(self, (x, y)):
		return self.m[y][x]

	def __setitem__(self, (x, y), o):
		self.m[y][x] = o
		return self.m[y][x]

	def update(self, fields):
		for f in fields:
			self[f.x, f.y] = f

	def get_islands(self):
		for j in range(0, self.dim):
			for i in range(0, self.dim):
				if self[i, j] is None:
					continue
				if self[i, j].t == 'LAND':
					yield self[i, j]


	def dump(self):
		lands = []
		waters = []
		for j in range(0, self.dim):
			for i in range(0, self.dim):
				if self[i, j] is None:
					continue
				if self[i, j].t == 'LAND':
					lands.append("%i %i %i" % (i, j, self[i, j].sticks))
				else:
					waters.append("%i %i %i" % (i, j))

		return '\n'.join(lands) + '\n', '\n'.join(waters) + '\n'

def dump_beetles(bet):
	lines = []
	for b in bet:
		lines.append("%i %i 0" % (b.x, b.y))
	return '\n'.join(lines) + '\n'


class Field(object):
	def __init__(self, x = 0, y = 0):
		self.x, self.y = x, y
		pass

	def __repr__(self):
		return self.t[0]

	def __str__(self):
		return "%s(%i, %i) st:%i, my:%i" % (repr(self), self.x, self.y, self.sticks, self.mysticks)


	@staticmethod
	def dist_key(f, x, y):
		if f.sticks - f.mysticks == 0:
			return 1000
		else:
			dist = abs(f.x - x) + abs(f.y - y)
			
	@staticmethod
	def dist_from(x, y):
		return lambda f: Field.dist_key(f, x, y)


class Connection(dl24.connection.Connection):
	# implementacja komend z zadania
	def desc(self):
		self.cmd_describe_world()
		a = self.readints(5)
		a = {
				'N': a[0],
				'I': a[1],
				'Smin': a[2],
				'F': a[3],
				'T': a[4],
		}
		a['K'] = self.readfloat()
		return a

	def ttr(self):
		self.cmd_time_to_rescue()
		a = {}
		a['fstatus'] = self.readstr()
		a['L'] = self.readint()
		a['islands'] = []
		for i in range(0, 5):
			isl = self.readints(3)
			a['islands'].append(isl)
		return a

	def ls(self):
		self.cmd_list_survivors()
		num = self.readint()
		for i in range(0, num):
			yield(self.readint())

	def info(self, n):
		self.cmd_info(n)
		a = Beetle(n)
		a.x, a.y = self.readints(2)
		a.sticks = self.readint()
		a.busy = self.readstr()
		try:
			a.busy = int(a.busy)
		except ValueError:
			a.busy = -1
		a.role = self.readstr()
		a.fields = {}
		for i in range(0, 5):
			t = self.readstr()
			if t != 'NIL':
				x, y = self.readints(2)
				a.fields[x, y] = Field(x, y)
				a.fields[x, y].t = t
				a.fields[x, y].info = self.readints(6)
		return a

	def ls_wood(self, n):
		self.cmd_list_wood(n)
		w = self.readint()
		fs = []
		for i in range(0, w):
			fs.append(Field())
			fs[-1].x, fs[-1].y = self.readints(2)
			fs[-1].sticks, fs[-1].mysticks = self.readints(2)
			fs[-1].t = 'LAND'
		return fs

	def take(self, n):
		self.cmd_take(n)

	def give(self, n):
		self.cmd_give(n)

	def move(self, n, x, y):
		self.cmd_move(n, x, y)

	def build(self, n):
		self.cmd_build(n)

def write_file(f, t):
	f = open('.'.join([str(universum), f]), "w")
	f.write(t)
	f.close()

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-U", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-D", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	return parser.parse_args()


class State:
	def __init__(self):
		pass

def init_state(read):
	global glob
	if read:
		glob = serializer.load()
	else:
		glob = State()


def loop(load_state):
	d = conn.desc()
	t = conn.ttr()
	beetle_nos = list(conn.ls())
	beetles = [conn.info(no) for no in beetle_nos]
	if load_state:
		for b in beetles:
			b.state = glob.bstates[b.n]
	print(d)
	print(t)
	if not load_state:
		glob.m = Map(d['N'])
	for b in beetles:
		if b.my_field.t == 'LAND':
			glob.m.update(conn.ls_wood(b.n))
	isl = list(glob.m.get_islands())

	for b in beetles:
		if b.busy > 0:
			continue
		if b.state['act'] == 'idle':
			if b.my_field.t == 'LAND':
				if glob.m[b.x, b.y] is not None and glob.m[b.x, b.y].sticks >= 100 and b.role == 'NONE':
					try:
						conn.build(b.n)
					except Exception as e:
						print(e)
				else:
					b.closest = max(filter(lambda f: (f.x, f.y) != (b.x, b.y), isl), key = Field.dist_from(b.x, b.y))
					b.state['route'] = [b.closest.x - b.x, b.closest.y - b.y]
					b.state['target'] = (b.x, b.y)
					b.state['act'] = 'take_wood'
			else:
				b.closest = max(filter(lambda f: (f.x, f.y) != (b.x, b.y), isl), key = Field.dist_from(b.x, b.y))
				b.state['route'] = [b.closest.x - b.x, b.closest.y - b.y]
				b.state['act'] = 'rescue'
		elif b.state['act'] == 'take_wood':
			if b.state['route'] == [0, 0]:
				try:
					conn.take(b.n)
				except Exception as e:
					print(e)
				b.state['act'] = 'go_back'
				b.state['route'] = [b.state['target'][0] - b.x, b.state['target'][1] - b.y]
			else:
				b.step(conn)
		elif b.state['act'] == 'go_back':
			if b.state['route'] == [0, 0]:
				try:
					conn.give(b.n)
				except Exception as e:
					print(e)
				b.state['act'] = 'idle'
			else:
				b.step(conn)
		elif b.state['act'] == 'rescue':
			if b.my_field.t == 'LAND': # saved!
				b.state['act'] = 'idle'
			else:
				b.step(conn)


	print_ar(beetles)

	lands, waters = glob.m.dump()
	write_file('lands', lands)
	write_file('waters', waters)
	write_file('beetles', dump_beetles(beetles))
	glob.bstates = {}
	for b in beetles:
		glob.bstates[b.n] = b.state
	# ~time.sleep(3)


if __name__ == '__main__':
	args = parse_args()
	config = Config(args.universum)
	global universum
	universum = args.universum
	serializer = Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	print info("logged in")

	init_state(args.loadstate)
	
	try: # main loop
		loop(args.loadstate)
		conn.wait()
		while 1:
			loop(True)
			conn.wait()
	except KeyboardInterrupt:
		serializer.save(glob)
	except:
		traceback.print_exc()
		serializer.save(glob, ".crash")
