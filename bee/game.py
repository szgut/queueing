from aux import *

from dl24.log import RED, MAGENTA, YELLOW, BLUE, GREEN, RESET

vals = {
		'J': 11,
		'Q': 12,
		'K': 13,
		'A': 14
}

suits = {
		'S': 0,
		'H': 1,
		'D': 2,
		'C': 3
}

class Card(object):
	S = 0
	H = 1
	D = 2
	C = 3

	colors = {
			S: RED,
			H: MAGENTA,
			D: YELLOW,
			C: GREEN
	}

	def __init__(self, s):
		try:
			self._val = int(s[:-1])
		except ValueError:
			self._val = vals[s[:-1]]
		self._suit = suits[s[-1]]

	def __eq__(self, o):
		return o.val == self.val and o.suit == self.suit

	def __ne__(self, o):
		return not self.__eq__(o)

	@property
	def suit(self):
		return self._suit

	@property
	def val(self):
		return self._val

	def __str__(self):
		return "%s%s" % (Card._pretty_val(self.val), Card._pretty_suit(self.suit))

	def __repr__(self):
		return Card.colors[self._suit] + self.__str__() + RESET

	@staticmethod
	def _pretty_val(val):
		if 2 <= val <= 10:
			return "%d" % val
		elif val <= 14:
			return reverse(vals)[val]
		else:
			raise ValueError("wrong val in _pretty_val!")

	@staticmethod
	def _pretty_suit(suit):
		if 0 <= suit <= 3:
			return reverse(suits)[suit]
		else:
			raise ValueError("wrong suit in _pretty_suit")


def select_mode(cards):
	if len(cards) != 8:
		raise ValueError("wrong number of cards during selection: %i!" % len(cards))
	quality = sum([c.val for c in cards]) / 8.0
	if quality >= 8:
		return 'A'
	else:
		return 'L'

def select_kitty(mode, cards):
	cards = sorted(cards, key=lambda c: c.val)
	if mode == 'A':
		# get rid of low cards
		return cards[:4]
	else:
		# get rid of high cards
		return cards[-4:]



def play_A(hand, table, left):
	if there_are(table):
		# adding a card
		suit = table[0].suit
		suited = filter(lambda c: c.suit == suit, hand)
		if there_are(suited):
			return play_A_suited(suited, suit, table, left)
		else:
			# no suited cards, choose worst
			return min_card(hand)
	else:
		# starting
		killers = []
		for suit in [Card.S, Card.H, Card.D, Card.C]:
			left_suit = filter(lambda c: c.suit == suit, left)
			hand_suit = filter(lambda c: c.suit == suit, hand)
			if (not there_are(left_suit)) and there_are(hand_suit):
				killers.append(min_card(hand_suit))
		if there_are(killers):
			print BLUE + "GOTCHA, you not has dat suit!!!" + RESET
			return min_card(killers)
		else:
			# no killers
			good = []
			for suit in [Card.S, Card.H, Card.D, Card.C]:
				left_suit = filter(lambda c: c.suit == suit, left)
				hand_suit = filter(lambda c: c.suit == suit, hand)
				if there_are(hand_suit):
					max_left = max_card(left_suit)
					good += filter(lambda c: c.val > max_left.val, hand_suit)
			if there_are(good):
				print BLUE + "GOTCHA, you not has dat suit so big!!!" + RESET
				return min_card(good)
			else:
				print RED + "will loose nearly for sure" + RESET
				return min_card(hand)

def play_A_suited(suited, suit, table, left):
	if len(table) == 1:
		greater_than_table = filter(lambda c: c.val > table[0].val, suited)
		if there_are(greater_than_table):
			max_opponent = max_card(left, only_suit=suit)
			if max_opponent is not None:
				max_opponent = max_opponent.val
			else:
				max_opponent = 0
			greater_than_op = filter(lambda c: c.val > max_opponent,
					greater_than_table)
			if there_are(greater_than_op):
				print BLUE + "about to win!!!" + RESET
				return min_card(greater_than_op)
			else:
				return max_card(greater_than_table)
		else:
			return min_card(suited)
	else:
		# last card, enough to put least better
		max_on_table = max_card(table, only_suit=suit)
		guarantees = filter(lambda c: c.val > max_on_table.val, suited)
		if there_are(guarantees):
			return min_card(guarantees)
		else:
			return min_card(suited)



def play_L(hand, table, left):
	if there_are(table):
		# adding a card
		suit = table[0].suit
		suited = filter(lambda c: c.suit == suit, hand)
		if there_are(suited):
			return play_L_suited(suited, suit, table, left)
		else:
			# no good cards, choose highest, because it's least valuable
			return max_card(hand)
	else:
		# starting
		no_suiciders = []
		for suit in [Card.S, Card.H, Card.D, Card.C]:
			left_suit = filter(lambda c: c.suit == suit, left)
			hand_suit = filter(lambda c: c.suit == suit, hand)
			if there_are(left_suit) and there_are(hand_suit):
				no_suiciders.append(min_card(hand_suit))
		#print "no_su: %s" % no_suiciders
		if there_are(no_suiciders):
			return min_card(no_suiciders)
		else:
			print RED + "doomed to fail:(" + RESET
			return max_card(hand)

def play_L_suited(suited, suit, table, left):
	if len(table) == 1:
		min_opponent = min_card(left, only_suit=suit)
		if min_opponent is not None:
			min_opponent = min_opponent.val
		else:
			min_opponent = 15
		less_than_op = filter(lambda c: c.val < min_opponent,
				suited)
		if there_are(less_than_op):
			print BLUE + "about to win!!!" + RESET
			return max_card(less_than_op)
		else:
			less_than_table = filter(lambda c: c.val < table[0].val, suited)
			if there_are(less_than_table):
				return max_card(less_than_table)
			else:
				return min_card(suited)
	else:
		table_max = max_card(table, only_suit=suit)
		less_than_table = filter(lambda c: c.val < table_max, suited)
		if there_are(less_than_table):
			return max_card(less_than_table)
		else:
			return max_card(suited)
