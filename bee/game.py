from aux import *

from dl24.log import RED, MAGENTA, YELLOW, GREEN, RESET

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



def play_A(hand, table):
	if there_are(table):
		# adding a card
		suit = table[0].suit
		suited = filter(lambda c: c.suit == suit, hand)
		if there_are(suited):
			return play_A_suited(suited, suit, table)
		else:
			# no suited cards, choose worst
			return min_card(hand)
	else:
		# starting
		return max_card(hand)

def play_A_suited(suited, suit, table):
	if len(table) < 2:
		return max_card(suited)
	else:
		# last card, enough to put least better
		suited_on_table = filter(lambda c: c.suit == suit, table)
		max_on_table = max(suited_on_table, key=lambda c: c.val)
		guarantees = filter(lambda c: c.val > max_on_table.val, suited)
		if there_are(guarantees):
			return min_card(guarantees)
		else:
			return min_card(suited)



def play_L(hand, table):
	if there_are(table):
		# adding a card
		suit = table[0].suit
		suited = filter(lambda c: c.suit == suit, hand)
		if there_are(suited):
			return play_L_suited(suited, suit, table)
		else:
			# no good cards, choose highest, because it's least valuable
			return max_card(hand)
	else:
		# starting
		return min_card(hand)

def play_L_suited(suited, suit, table):
		suited_on_table = filter(lambda c: c.suit == suit, table)
		max_on_table = max_card(suited_on_table)
		# find the highest which is lower than max suited on table
		guarantees = filter(lambda c: c.val < max_on_table.val, suited)
		if there_are(guarantees):
			return max_card(guarantees)
		else:
			# can't assert win :(
			if len(table) < 2:
				# put lowest, hoping someone will play higher
				return min_card(suited)
			else:
				# use highest, we're loosing anyway
				return max_card(suited)
