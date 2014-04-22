def reverse(d):
	return {v: k for k, v in d.items()}

def str_cards(cards):
	return ' '.join(map(repr, cards))

