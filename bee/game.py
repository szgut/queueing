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

def play_A(hand, table):
	if len(table) != 0:
		# adding a card
		suit = table[0].suit
		suited = filter(lambda c: c.suit == suit, hand)
		if len(suited) == 0:
			# no good cards, choose worst
			return min(hand, key=lambda c: c.val)
		else:
			return max(suited, key=lambda c: c.val)
	else:
		# starting
		return max(hand, key=lambda c: c.val)
