def reverse(d):
	return {v: k for k, v in d.items()}

def str_cards(cards):
	return ' '.join(map(repr, cards))

def there_are(collection):
	return len(collection) != 0

def min_card(cards, only_suit = None):
	if only_suit is not None:
		filtered = filter(lambda c: c.suit == only_suit, cards)
	else:
		filtered = cards
	if not there_are(filtered):
		return None
	return min(filtered, key=lambda c: c.val)

def max_card(cards, only_suit = None):
	if only_suit is not None:
		filtered = filter(lambda c: c.suit == only_suit, cards)
	else:
		filtered = cards
	if not there_are(filtered):
		return None
	return max(filtered, key=lambda c: c.val)

values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
suits = ['S', 'H', 'D', 'C']
def all_cards():
	return [x+y for x in values for y in suits]
