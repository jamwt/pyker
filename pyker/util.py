(
HAND_HIGH,
HAND_PAIR,
HAND_TWOPAIR,
HAND_TRIPS,
HAND_STRAIGHT,
HAND_FLUSH,
HAND_FULLHOUSE,
HAND_QUADS,
HAND_STRAIGHT_FLUSH,
HAND_ROYAL_FLUSH,
) = range(10)

def suit(c):
	return c[1]

def card(c):
	return c[0]

_ctn = {
	'T' : 10,
	'J' : 11,
	'Q' : 12,
	'K' : 13,
	'A' : 14,
}

_srank = dict(S=4, H=3, C=2, D=1)

def card_to_num(c):
	try:
		return _ctn[c]
	except:
		return int(c)

def card_compare(c1, c2):
	return cmp(card_to_num(card(c1)), card_to_num(card(c2)))

def suit_compare(c1, c2):
	return cmp(_srank[suit(c1)], _srank[suit(c2)])

def make_combinations(s, num):
	if num == 0:
		yield []
	else:
		for i in xrange(len(s)):
			for combs in make_combinations(s[i+1:], num - 1):
				yield [s[i]] + combs

def make_split_amounts(amt, count):
	amounts = [amt / count] * count
	for x in xrange(0, amt % count):
		amounts[x] += 1
	return amounts

def next_extant_player(pos, active_players, last=False):
	psort = active_players[:]
	def sort_key(x):
		r = x - pos
		if r <= 0:
			r += 10000
		return r

	psort.sort(key=sort_key)
	if last:
		if pos in active_players:
			return psort[-2]
		else:
			return psort[-1]
	else:
		return psort[0]
