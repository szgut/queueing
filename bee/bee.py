#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import traceback

from dl24 import connection
from dl24 import log
from dl24 import misc

from time import sleep

from aux import *
from game import *


class Config(object):
	def __init__(self, universum=1):
		self.host = 'universum.dl24'
		self.datafile = 'data' + str(universum)
		self.port = 20000+universum-1


class Statistic(object):
	def __init__(self):
		self.wins = 0
		self.losses = 0
		self.run_wins = 0
		self.run_losses = 0
		self.round_wins = 0
		self.round_losses = 0

	def collect_win(self):
		self.wins += 1
		self.run_wins += 1
		self.round_wins += 1

	def collect_loss(self):
		self.losses += 1
		self.run_losses += 1
		self.round_losses += 1

	def new_round(self):
		self.round_wins = self.round_losses = 0

	def new_run(self):
		self.run_wins = self.run_losses = 0

	def ratio_str(self, wins, losses):
		if losses != 0:
			ratio = wins*1.0 / losses
		else:
			ratio = "-"
		return ("%s ("+GREEN+"%i"+RESET+"/"+RED+"%i"+RESET+")") % (
				ratio,
				wins, losses)

	def __str__(self):
		s = ""
		s += "\twin/loss ratio  : " + self.ratio_str(self.wins, self.losses) + "\n"
		s +=  "\t\t run    : " + self.ratio_str(self.run_wins,   self.run_losses) + "\n"
		s +=  "\t\t round  : " + self.ratio_str(self.round_wins, self.round_losses) + "\n"
		return s


class Connection(connection.Connection):
	def read_cards(self, read_num = True):
		if read_num:
			line = self.readline()
			num = int(line.strip())
		else:
			num = 1 # doesn't matter
		if num != 0:
			line = self.readline()
			# "no trick played ... bla bla"
			if line[:2] in ["no", "ga"]:
				return None
			return map(Card, line.strip().split(' '))
		else:
			return []

	# implementacja komend z zadania
	def get_state(self):
		self.cmd("get_state")
		return self.readline().strip()

	def get_my_id(self):
		self.cmd("get_my_id")
		return int(self.readline())

	def get_my_cards(self):
		self.cmd("get_my_cards")
		return self.read_cards()

	def select_game(self, t):
		if t not in ['A', 'L']:
			raise ValueError("attempt to choose wrong game type")
		try:
			self.cmd("select_game", t)
		except connection.CommandFailedError:
			print "warning: cannot select mode, already selected this one..."

	def select_kitty(self, cards):
		if len(cards) != 4:
			raise ValueError("wrong number of cards, got %i, expected 4" % len(cards))
		self.cmd("select_kitty", map(str, cards))

	def current_game(self):
		self.cmd("current_game")
		return self.readline().strip()

	def selector_id(self):
		self.cmd("selector_id")
		return int(self.readline())

	def turn_id(self):
		self.cmd("turn_id")
		return int(self.readline())

	def on_table(self):
		self.cmd("on_table")
		return self.read_cards()

	def play(self, card):
		self.cmd("play", str(card))

	def last_trick(self):
		self.cmd("last_trick")
		trick = self.read_cards(read_num = False)
		if trick is not None:
			fst_player, winner = map(int, self.readline().strip().split(' '))
			return (trick, fst_player, winner)
		else:
			return (None, None, None)

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
		self.stat = Statistic()


def init_state(read):
	global gs
	if read:
		gs = serializer.load()
		gs.stat.new_round()
		gs.stat.new_run()
	else:
		gs = PersistentState()


def update_win_stat(last_mode, my_last_id):
	global gs
	global prev_trick
	trick, fst_player, winner = conn.last_trick()
	if trick is not None:
		print "---------------------------------------------------------"
		print "last trick: %s, started:%i winner:%i" % (
				str_cards(trick), fst_player, winner)
		print
		if last_mode == 'A' and winner == my_last_id:
			print GREEN + "\t\t\tWON!!! (took a trick)" + RESET
			gs.stat.collect_win()
		elif last_mode == 'A' and winner != my_last_id:
			print RED + "\t\t\tLOST (someone took trick)" + RESET
			gs.stat.collect_loss()
		elif last_mode == 'L' and winner == my_last_id:
			print RED + "\t\t\tLOST (took trick, shouldn't have:()" + RESET
			gs.stat.collect_loss()
		elif last_mode == 'L' and winner != my_last_id:
			print GREEN + "\t\t\tWON!!! (didn't take trick)" + RESET
			gs.stat.collect_win()
		print gs.stat
		print
	else:
		print "cannot retrieve who won, ignoring..."

cycle = -100

def loop():
	global gs
	global cycle

	st = conn.get_state()

	if st == 'GAME_SELECTION':
		gs.stat.new_round()
		me = conn.get_my_id()
		selector_id = conn.selector_id()
		if me == selector_id:
			my_cards = conn.get_my_cards()
			mode = select_mode(my_cards)
			print "my 8 cards: %s" % str_cards(my_cards)
			print "selecting %s" % mode
			conn.select_game(mode)
		else:
			print "someone is selecting mode..."
	elif st == 'KITTY_SELECTION':
		cycle = 0
		me = conn.get_my_id()
		selector_id = conn.selector_id()
		mode = conn.current_game()
		if me == selector_id:
			my_cards = conn.get_my_cards()
			kitty = select_kitty(mode, my_cards)
			print "my 20 cards: %s" % str_cards(my_cards)
			print "selecting kitty: %s" % str_cards(kitty)
			conn.select_kitty(kitty)
		else:
			print "someone is selecting kitty..."
	elif st == 'TRICK':
		me = conn.get_my_id()
		mode = conn.current_game()
		if cycle == 3:
			update_win_stat(last_mode=mode, my_last_id=me)
		my_cards = conn.get_my_cards()
		on_table = conn.on_table()

		plays = conn.turn_id()
		selector_id = conn.selector_id()
		if plays == me:
			col = RED
		else:
			col = RESET
		print "%s%s me:%i plays:%i, sel:%i %s" % (col,
				mode, me,
				plays, selector_id, RESET)
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
		else:
			print "someone playing now..."

		cycle += 1
		if cycle > 3:
			cycle = 1

		if cycle == 3 and ((plays == me and len(my_cards) == 1) or (plays != me and len(my_cards) == 0)):
			update_win_stat(last_mode=mode, my_last_id=me)
	else:
		print "BREAK STATE"


if __name__ == '__main__':
	args = parse_args()
	print args.posargs
	config = Config(args.universum)
	serializer = misc.Serializer(config.datafile)
	conn = Connection(config.host, config.port)
	log.info("logged in")

	init_state(args.loadstate)

	try: # main loop
		while 1:
			loop()
			conn.wait()
	except KeyboardInterrupt:
		serializer.save(gs)
	except:
		traceback.print_exc()
		serializer.save(gs, ".crash")
