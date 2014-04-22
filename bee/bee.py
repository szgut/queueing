#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import traceback

from dl24 import connection
from dl24 import log
from dl24 import misc

from aux import *
from game import *


class Config(object):
	def __init__(self, universum=1):
		self.host = 'universum.dl24'
		self.datafile = 'data'
		self.port = 20000+universum-1


class Connection(connection.Connection):
	def read_cards(self, read_num = True):
		if read_num:
			num = self.readint()
		else:
			num = 1 # doesn't matter
		if num != 0:
			return map(Card, self.readline().strip().split(' '))
		else:
			return []

	# implementacja komend z zadania
	def get_state(self):
		self.cmd("get_state")
		return self.readstr()

	def get_my_id(self):
		self.cmd("get_my_id")
		return self.readint()

	def get_my_cards(self):
		self.cmd("get_my_cards")
		return self.read_cards()

	def select_game(self, t):
		if t not in ['A', 'L']:
			raise ValueError("attempt to choose wrong game type")
		self.cmd("select_game", t)

	def select_kitty(self, cards):
		if len(cards) != 4:
			raise ValueError("wrong number of cards, got %i, expected 4" % len(cards))
		self.cmd("select_kitty", map(str, cards))

	def current_game(self):
		self.cmd("current_game")
		return self.readstr().strip()

	def selector_id(self):
		self.cmd("selector_id")
		return self.readint()

	def turn_id(self):
		self.cmd("turn_id")
		return self.readint()

	def on_table(self):
		self.cmd("on_table")
		return self.read_cards()

	def play(self, card):
		self.cmd("play", str(card))

	def last_trick(self):
		self.cmd("last_trick")
		trick = self.read_cards(read_num = False)
		fst_player, winner = self.readints(2)
		return (trick, fst_player, winner)

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


write_trick_next_time = False
my_last_id = 0
last_mode = None
def loop():
	global write_trick_next_time
	global my_last_id
	global last_mode

	st = conn.get_state()
	if write_trick_next_time:
		write_trick_next_time = False
		if st == 'TRICK':
			trick, fst_player, winner = conn.last_trick()
			print "last trick: %s, started:%i winner:%i" % (
					str_cards(trick), fst_player, winner)
			if last_mode == 'A' and winner == my_last_id:
				print GREEN + "WON!!! (took a trick)" + RESET
			elif last_mode == 'A' and winner != my_last_id:
				print YELLOW + "didn't win (someone took trick)"
			elif last_mode == 'L' and winner == my_last_id:
				print RED + "Oh, noez, took trick, shouldn't have:(" + RESET
			elif last_mode == 'L' and winner != my_last_id:
				print GREEN + "WON!!! (didn't take trick)" + RESET
		else:
			print "game finished, not checking who took the trick"

	print '---'
	if st != 'TRICK':
		print "not supported state"
	else:
		me = conn.get_my_id()
		mode = conn.current_game()
		plays = conn.turn_id()
		selector_id = conn.selector_id()
		if plays == me:
			col = RED
		else:
			col = RESET
		print "%s%s me:%i plays:%i, sel:%i %s" % (col,
				mode, me,
				plays, selector_id, RESET)
		my_cards = conn.get_my_cards()
		on_table = conn.on_table()
		if len(on_table) == 2:
			write_trick_next_time = True
			my_last_id = me
			last_mode = mode
		print "my cards: %s" % str_cards(my_cards)
		print "table:    %s" % str_cards(on_table)
		if plays == me:
			if mode == 'A':
				to_play = play_A(hand = my_cards, table = on_table)
			else:
				to_play = play_L(hand = my_cards, table = on_table)
			print "playing %s" % str(to_play)
			if to_play is not None:
				conn.play(to_play)


if __name__ == '__main__':
	args = parse_args()
	print args.posargs
	config = Config(args.universum)
	serializer = misc.Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	log.info("logged in")

	init_state(args.loadstate)
	gs.a += 1
	print gs.a

	try: # main loop
		while 1:
			loop()
			conn.wait()
	except KeyboardInterrupt:
		serializer.save(gs)
	except:
		traceback.print_exc()
		serializer.save(gs, ".crash")
