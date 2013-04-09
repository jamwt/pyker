from pyker.util import *

_shorthand = {
	HAND_HIGH : 'high',
	HAND_PAIR : 'pair',
	HAND_TWOPAIR : '2pair',
	HAND_TRIPS : 'trips',
	HAND_STRAIGHT : 'straight',
	HAND_FLUSH : 'flush',
	HAND_FULLHOUSE : 'full',
	HAND_QUADS : 'quads',
	HAND_STRAIGHT_FLUSH : 'stfl',
	HAND_ROYAL_FLUSH : 'royal',
}

class HandToLanguage:
	cards = {}
	def get_hand(self, hand):
		m = getattr(self, 'hand_%s' % _shorthand[hand[0]])
		return m(*tuple(hand[1:]))

	def conv_card(self, c, plural=False):
		return self.cards[c][int(plural)]

class HTL_en(HandToLanguage):
	cards = {
		2 : ('two', 'twos'),
		3 : ('three', 'threes'),
		4 : ('four', 'fours'),
		5 : ('five', 'fives'),
		6 : ('six', 'sixes'),
		7 : ('seven', 'sevens'),
		8 : ('eight', 'eights'),
		9 : ('nine', 'nines'),
		10 : ('ten', 'tens'),
		11 : ('jack', 'jacks'),
		12 : ('queen', 'queens'),
		13 : ('king', 'kings'),
		14 : ('ace', 'aces'),
	}

	def hand_high(self, card, *kicks):
		cc = self.conv_card
		return "%s high" % (cc(card),)

	def hand_pair(self, card, kicker, *kicks):
		cc = self.conv_card
		return "a pair of %s, %s kicker" % (cc(card, True), cc(kicker))

	def hand_2pair(self, p1, p2, *kicks):
		cc = self.conv_card
		return "two pair of %s and %s" % (cc(p1,True), cc(p2, True),)

	def hand_trips(self, card, *kicks):
		cc = self.conv_card
		return "a set of %s" % (cc(card, True),)

	def hand_straight(self, card):
		cc = self.conv_card
		return "a straight to the %s" % (cc(card),)

	def hand_flush(self, high):
		cc = self.conv_card
		return "%s high flush" % (cc(high),)

	def hand_full(self, set, pair):
		cc = self.conv_card
		return "full house, %s full of %s" % (cc(set, True), cc(pair, True))

	def hand_quads(self, card, *kicks):
		cc = self.conv_card
		return "quad %s" % (cc(card, True),)

	def hand_stfl(self, card):
		cc = self.conv_card
		return "a straight flush to the %s" % (cc(card),)

	def hand_royal(self):
		return "a royal flush"

_lang_to_htl = {
	'en' : HTL_en(),
}

_curlang = ['en']

def set_language(lang):
	assert lang in _lang_to_htl
	_curlang[0] = lang

def get_language():
	return _curlang[0]

def get_hand_phrase(hand):
	return _lang_to_htl[get_language()].get_hand(hand)
