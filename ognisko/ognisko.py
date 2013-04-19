#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import dl24.connection
from dl24.misc import Serializer
from dl24.misc import delay_sigint
from dl24.colors import warn, bad, good, info
import argparse
import traceback

class Config(object):
	def __init__(self, universum=1):
		self.host = 'universum.dl24'
		self.datafile = 'data'
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
		self.n = n
		pass

	def __repr__(self):
		  return "B%i(%i, %i)\tst:%i busy:%i %s" % (self.n, self.x, self.y, self.sticks, self.busy, self.role)

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


class Map(object):
	def __init__(self, x, y):
		self.m = []
		for i in range(0, y):
			line = []
			for j in range(0, x):
				line.append(Field(j, i))
			self.m.append(line)

class Field(object):
	def __init__(self, x = 0, y = 0):
		self.x, self.y = x, y
		pass

	def __repr__(self):
		return self.t[0]

	def __str__(self):
		return "%s(%i, %i) st:%i, my:%i" % (repr(self), self.x, self.y, self.sticks, self.mysticks)


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
			fs[-1].t = 'WATER'
		return fs


def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-U", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-D", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	return parser.parse_args()

def init_state(read):
	global global_sth
	if read:
		global_sth = serializer.load()
	else:
		global_sth = 0


zmienna_statyczna = [1]
def loop():
	# ~import time
	# ~print "."
	zmienna_statyczna[0] += 1
	d = conn.desc()
	t = conn.ttr()
	beetle_nos = list(conn.ls())
	beetles = [conn.info(no) for no in beetle_nos]
	print(d)
	print(t)
	print_ar(beetles)
	print_sq(beetles[0].f())
	fields = conn.ls_wood(beetle_nos[0])
	for f in fields:
		print(str(f))
	# ~time.sleep(3)


if __name__ == '__main__':
	args = parse_args()
	config = Config(args.universum)
	serializer = Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	print info("logged in")

	init_state(args.loadstate)
	global_sth += 1
	print global_sth
	
	try: # main loop
		while 1:
			loop()
			conn.wait()
	except KeyboardInterrupt:
		serializer.save(global_sth)
	except:
		traceback.print_exc()
		serializer.save(global_sth, ".crash")
