def reverse(d):
	return {v: k for k, v in d.items()}

def str_cards(cards):
	return ' '.join(map(repr, cards))

def there_are(collection):
	return len(collection) != 0

def min_card(cards, suit = None):
	if suit is not None:
		filtered = filter(lambda c: c.suit == suit, cards)
	else:
		filtered = cards
	if not there_are(filtered):
		return None
	return min(filtered, key=lambda c: c.val)

def max_card(cards, suit = None):
	if suit is not None:
		filtered = filter(lambda c: c.suit == suit, cards)
	else:
		filtered = cards
	return max(filtered, key=lambda c: c.val)
