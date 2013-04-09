CARDS = [
	'2',
	'3',
	'4',
	'5',
	'6',
	'7',
	'8',
	'9',
	'T',
	'J',
	'Q',
	'K',
	'A',
]

SUITES = [
	'S',
	'C',
	'D',
	'H',
]

REF_DECK = []
for _c in CARDS:
	for _s in SUITES:
		REF_DECK.append('%s%s' % (_c, _s))

import random
class Deck:
	def collect_shuffle(self):
		self.deck = REF_DECK[:]
		random.shuffle(self.deck)

	def deal(self, players, count):
		for c in xrange(count):
			for player in players:
				player.give_card(self.get_card())

	def get_card(self):
		return self.deck.pop()
