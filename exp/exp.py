#!/usr/bin/env python
import readline
import sys
import threading
import wdx

from dl24 import connection

class Connection(connection.Connection):
	def maze(self):
		print "maze"
		self.cmd("maze")
		wi = self.readint()
		he = self.readint()
		wdx.set_dims(wi, he);
		self.exists = True
		for x in xrange(he):
			wdx.push_row(self.readstr())
	
	def treasures(self):
		self.cmd("treasures")
		n = self.readint()
		wdx.clear_treasures()
		for i in xrange(n):
			x = self.readint()
			y = self.readint()
			v = self.readfloat()
			wdx.add_treasure(x, y, v)
	
	def monsters(self):
		self.cmd("monsters")
		n = self.readint()
		wdx.clear_monsters()
		for i in xrange(n):
			x = self.readint()
			y = self.readint()
			a = self.readint()
			v = self.readfloat()
			wdx.add_monster(x, y, a, v)
	
	def others(self):
		self.cmd("all_explorers")
		n = self.readint()
		wdx.clear_others()
		for i in xrange(n):
			x = self.readint()
			y = self.readint()
			a = self.readint()
			wdx.add_other(x, y ,a)
	
	def mine(self):
		self.cmd("my_explorers")
		n = self.readint()
		wdx.clear_mine()
		l = list()
		for i in xrange(n):
			id = self.readint()
			x = self.readint()
			y = self.readint()
			a = self.readint()
			w = self.readfloat()
			u = self.readint()
			v = self.readfloat()
			c = self.readfloat()
			b = self.readint()
			l.append(id)
			wdx.add_mine(id, x, y, a, w, u, v, c, b)
		return l
	
	def equipment(self):
		self.cmd("equipment")
		n = self.readint()
		wdx.clear_eq()
		for i in xrange(n):
			id = self.readint()
			p = self.readfloat()
			a = self.readint()
			w = self.readfloat()
			wdx.add_eq(id, p, a, w)
	
	def ttc(self):
		self.cmd("time_to_change")
		ttch = self.readint()
		ttco = self.readint()
		wdx.set_ttc(ttco)
		return (ttch, ttco)

def main(uni):
	conn = Connection("universum.dl24", 20004+int(uni))
	conn.exists = False
	wdx.paint()
	ttch = -1
	ttco = -1
	while True:
		(nttch, nttco) = conn.ttc()
		print nttch, "/", nttco
		if nttco > ttco:
			conn.exists = False
		if nttch > ttch or nttco > ttco:
			while True:
				try:
					conn.maze()
					break
				except connection.CommandFailedError as e:
					if e.errno == 115 and (conn.exists == False or nttch >= 15):
						conn.wait()
						pass
					else:
						break
			conn.equipment()
		(ttch, ttco) = (nttch, nttco)
		conn.treasures()
		conn.monsters()
		conn.others()
		eids = conn.mine()
		wdx.paint()
		wdx.assign()
		for id in eids:
			try:
				m = wdx.get_move(id)
				if m.kind == 0:
					print "move", m.dx, m.dy
					conn.cmd("move", id, m.dx, m.dy)
				if m.kind == 1:
					conn.cmd("take_treasure", id, m.value)
				if m.kind == 3:
					conn.cmd("buy_weapon", id, m.weapon)
			except Exception as e:
				print e
		conn.wait()

if __name__ == '__main__':
	try:
		readline.read_history_file()
	except IOError:
		print >> sys.stderr, 'touchnij se ~/.history'
	main(*sys.argv[1:])
	readline.write_history_file()
