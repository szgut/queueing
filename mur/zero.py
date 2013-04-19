#!/usr/bin/python2

#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import dl24.connection
from dl24.misc import Serializer
from dl24.misc import delay_sigint
from dl24.colors import warn, bad, good, info
import argparse
import traceback
import numpy as np
from datetime import datetime
from threading import Thread

class RejectedBrick(Exception): pass
class RejectedMatch(RejectedBrick): pass
class RejectedHeight(RejectedBrick): pass

ROTS = [
	(0,0,0),
	(1,0,0),
	(2,0,0),
	(3,0,0),
	
	(0,2,0),
	(1,2,0),
	(2,2,0),
	(3,2,0),
	
	(0,1,0),
	(1,0,1),
	(2,3,0),
	(3,0,3),
	
	(1,1,0),
	(2,0,1),
	(3,3,0),
	(0,0,3),
	
	(2,1,0),
	(3,0,1),
	(0,3,0),
	(1,0,3),
	
	(3,1,0),
	(0,0,1),
	(1,3,0),
	(2,0,3),
]

ROTS_ARRS = None



def r2a(how):
	def _sin(x): return [0,1,0,-1][x]
	def _cos(x): return [1,0,-1,0][x]
	def _shift(a, b, c): return np.matrix(
		[[1, 0, 0, a*(gs.world.D-1)],
		 [0, 1, 0, b*(gs.world.D-1)],
		 [0, 0, 1, c*(gs.world.D-1)],
		 [0, 0, 0, 1]]
	)
	(xy, xz, yz) = how
	return _shift(0, 1, 1) * np.matrix(
		[[1, 0, 0, 0],
		 [0, _cos(yz), -_sin(yz), 0],
		 [0, _sin(yz), _cos(yz), 0],
		 [0, 0, 0, 1]]
	) * _shift(0, -1, -1) * _shift(1, 0, 1) * np.matrix(
		[[_cos(xz), 0, -_sin(xz), 0],
		 [0, 1, 0, 0],
		 [_sin(xz), 0, _cos(xz), 0],
		 [0, 0, 0, 1]]
	) * _shift(-1, 0, -1) * _shift(1, 1, 0) * np.matrix(
		[[_cos(xy), -_sin(xy), 0 , 0],
		 [_sin(xy), _cos(xy), 0, 0],
		 [0, 0, 1, 0],
		 [0, 0, 0, 1]]
	) * _shift(-1, -1, 0)

def rot(lilis, matrix):
	wynik = np.empty([gs.world.D, gs.world.D, gs.world.D], dtype=int)
	for z in range(gs.world.D):
		for y in range(gs.world.D):
			for x in range(gs.world.D):
				v = matrix * np.matrix([[2*x], [2*y], [2*z], [1]])
				wynik[v[2][0]>>1, v[1][0]>>1, v[0][0]>>1] = 1 if lilis[z][y][x]  == '#' else 0
	return wynik
	

class Config(object):
	def __init__(self, universum=1):
		self.host = 'universum.dl24'
		self.datafile = 'data' + str(universum)
		self.port = 20004+universum-1

class Connection(dl24.connection.Connection):
	def describe(self):
		self.cmd_describe_world()
		w = World()
		w.X = conn.readint()
		w.Y = conn.readint()
		w.Z = conn.readint()
		w.D = conn.readint()
		w.B = conn.readint()
		w.R = conn.readint()
		w.Cv = conn.readfloat()
		w.Cp = conn.readfloat()
		w.T = conn.readint()
		w.K = conn.readfloat()
		return w
	
	def drop(self, x):
		(raz, dwa, x, y) = x
		x = (raz, dwa, x+1, y+1)
		self.cmd_drop_brick(x)
		blah = self._readstr_assert(['ACCEPTED', 'REJECTED_HEIGHT', 'REJECTED_MATCH'])
		if blah == 'ACCEPTED': return self.readfloat()
		elif blah == 'REJECTED_HEIGHT': raise RejectedHeight
		else: raise RejectedMatch
	
	def bricks(self):
		self.cmd_list_bricks()
		return self.readints(gs.world.B)
	
	def brick(self, x):
		self.cmd_show_brick(x)
		w = self.readfloat()
		pmin = self.readint()
		def _getslice():
			li = [ self.readline() for x in range(gs.world.D) ]
			li.reverse()
			return li
		li = [ _getslice() for x in range(gs.world.D) ]
		li.reverse()
		return Brick(w, pmin, li)
	
	def above(self):
		self.cmd_view_from_above()
		li = [ [conn.readint() for x in range(gs.world.X)] for x in range(gs.world.Y)]
		li.reverse()
		return np.matrix(li)


class Brick(object):
	def __init__(self, w, pmin, d):
		self.w = w
		self.pmin = pmin
		self.d = d
	
	def __str__(self): return str((self.w, self.pmin, self.d))
	
	def __repr__(self): return self.__str__()


class State(object):
	def __init__(self):
		self.bricks = dict()
	
	def allposs(self):
		D = self.world.D
		X = self.world.X
		Y = self.world.Y
		Z = self.world.Z
		for bid in self.abids:
			brick = self.bricks[bid]
			
			bylo = set()
			
			for rotid in range(len(ROTS_ARRS)):
				rorbri = rot(brick.d, ROTS_ARRS[rotid])
				if (str(rorbri) in bylo):
					continue
				bylo.add(str(rorbri))
				volume = rorbri.sum()
				
				himap = np.empty([D, D], dtype=int)
				shadow = np.empty([D, D], dtype=int)
				ones = np.empty([D, D], dtype=int)
				himap.fill(0)
				shadow.fill(0)
				ones.fill(1)
				volume = 0
				for z in range(D):
					for y in range(D):
						for x in range(D):
							if rorbri[z,y,x] == 1:
								shadow[y,x] = 1
							if shadow[y,x] == 0:
								himap[y,x] += 1
				himap = himap + (ones - shadow) * self.world.Z
				
				def _get(obj, x, y):
					try:
						return obj[y,x]
					except IndexError:
						return 0
				
				for x in range(X - D + 1):
					for y in range(Y - D + 1):
						slajs = self.above[y:y+D, x:x+D]
						h0 = (slajs - himap).max()
						touches = ((himap + h0) == slajs).sum()
						if touches >= brick.pmin and h0 + D <= Z:
							yield (brick.w * (self.world.Cv * volume + self.world.Cp * touches),
								(bid, ROTS[rotid], x, y)
							)

class World(object):
	pass

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-U", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-D", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	return parser.parse_args()

def init_state(read):
	global gs
	if read:
		gs = serializer.load()
	else:
		gs = State()


class Napykalacz(Thread):
	def run(self):
		while napykalam:
			try:
				global lista
				global lid
				print info('szukam')
				lista = list(sorted(gs.allposs(), key = lambda x: -x[0]))
				print good('Nowa lista!')
			except:
				pass

zmienna_statyczna = [1]
napykalam = False
lid = 0
lista = []
def loop():	
	with delay_sigint():
		print info('world')
		gs.world = conn.describe()
		global ROTS_ARRS
		ROTS_ARRS = [ r2a(x) for x in ROTS ]
		print info('jakie klocki')
		gs.abids = conn.bricks()
		for x in gs.abids:
			if x not in gs.bricks:
				print info('brak mi ' + str(x))
				gs.bricks[x] = conn.brick(x)
	
	print info('spogladam z gory')
	gs.above = conn.above()
	
	global napykalam
	global lista
	if napykalam == False:
		napykalam = True
		Napykalacz().start()
	olid = lid
	zuzylem = 0
	for z in lista[:gs.world.R]:
		try:
			print info('probuje zrzucic ' + str(z))
			print good(str(conn.drop(z[1])) + ' pkt')
			break
		except RejectedBrick:
			pass
		except:
			pass
	if olid == lid:
		lista = lista[zuzylem:]


if __name__ == '__main__':
	args = parse_args()
	config = Config(args.universum)
	serializer = Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	print info("logged in")

	init_state(args.loadstate)
	
	try: # main loop
		conn.wait()
		while 1:
			loop()
			conn.wait()
	except KeyboardInterrupt:
		serializer.save(gs)
	except:
		traceback.print_exc()
		serializer.save(gs, ".crash")
	napykalam = False

else:
	gs = State()
	gs.world = World()
	gs.world.D = 2

