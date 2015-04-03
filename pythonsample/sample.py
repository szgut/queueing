#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
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

	def round_no(self):
		return 1
		

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--universum", metavar="N", type=int, 
		help="universum number", default=1)
	parser.add_argument("-d", "--dontload", action='store_false', 
		help="do not load initial state from dump file", dest='loadstate')
	parser.add_argument('posargs', nargs='*', default=[])
	return parser.parse_args()


class Clicker(gui.Clicker):
	
	def __call__(self, click):
		print "CLICK", click.point, click.button


class WorldMap(object):
	
	def __init__(self):
		pass
		
	def tick(self):
		pass
	
	def draw_land(self):
		worker.command(tid=0, points=[tuple(island.pos) for island in self.islands],
					   color=Color.BROWN)


def loop():
	read_time()
	log.info("round %d" % round_no)
	
	if 'nobuild' not in args.posargs:
		pass
	
	world_map.tick()
	
	worker.command(action='clear')
	world_map.draw_land()


def init_state(load=False):
	global world_map, round_no
	if load:
		world_map, round_no = serializer.load()
	else:
		world_map = WorldMap()
		round_no = conn.round_no()


def read_time():
	global round_no
	old_round_no = round_no
	round_no = conn.round_no()
	if round_no > old_round_no:
		init_state()


if __name__ == '__main__':
	args = parse_args()
	print args.posargs
	config = Config(args.universum)
	serializer = misc.Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	log.info("logged in")

	worker = gui.Worker(title='SEA-%d' % args.universum, clicker=Clicker())
	init_state(args.loadstate)
	
	try: # main loop
		while 1:
			try:
				loop()
			except connection.ForcedWaitingError:
				print "skipping wait"
			else:
				conn.wait()
	except KeyboardInterrupt:
		serializer.save((world_map, round_no))
	except:
		traceback.print_exc()
		serializer.save((world_map, round_no), ".crash")
