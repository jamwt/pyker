from pyker.util import *

class HandMeta:
	def __init__(self, cards):
		self.cards = cards

	def make_groups(self):
		gs = {}
		for c in self.cards:
			try:
				gs[card(c)] += 1
			except KeyError:
				gs[card(c)] = 1
		self.groups = gs

	def make_seq(self):
		nums = list(set([card_to_num(card(c)) for c in self.cards]))
		if len(nums) != 5:
			self.seq = None
		else:
			nums.sort()
			if nums[-1] - nums[0] == 4:
				self.seq = nums[-1]
			else:
				# Ace Low
				nums = [(num == 14 and 1 or num) for num in nums]
				nums.sort()
				if nums[-1] - nums[0] == 4:
					self.seq = nums[-1]
				else:
					self.seq = None

	def check_flush(self):
		cs = None
		for c in self.cards:
			s = suit(c)
			if cs and s != cs:
				self.flush = False
				return
			elif not cs:
				cs = s
		self.flush = True

	def groups_by_value(self):
		keys = self.groups.keys()
		def group_sort(a, b):
			r = cmp(self.groups[a], self.groups[b])
			if r:
				return r
			return cmp(card_to_num(a), card_to_num(b))

		keys.sort(group_sort)
		keys.reverse()
		return [(card_to_num(k), self.groups[k]) for k in keys]

	def determine_hand(self):
		ordered_groups = self.groups_by_value()
		if self.seq and self.flush:
			# Royal flush
			if self.seq == card_to_num('A'):
				hand = HAND_ROYAL_FLUSH
				self.score = (hand,)
			# Straight flush
			else:
				hand = HAND_STRAIGHT_FLUSH
				self.score = (hand, self.seq)
		elif len(ordered_groups) == 2:
			if ordered_groups[0][1] == 4:
				hand = HAND_QUADS
				self.score = (hand, ordered_groups[0][0], ordered_groups[1][0])
			else:
				hand = HAND_FULLHOUSE
				self.score = (hand, ordered_groups[0][0], ordered_groups[1][0])
		elif self.flush:
			hand = HAND_FLUSH
			self.score = (hand, ordered_groups[0][0])
		elif self.seq:
			hand = HAND_STRAIGHT
			self.score = (hand, self.seq)
		elif ordered_groups[0][1] == 3:
			hand = HAND_TRIPS
			self.score = (hand, ordered_groups[0][0], ordered_groups[1][0], ordered_groups[2][0])
		elif ordered_groups[0][1] == 2 and ordered_groups[1][1] == 2:
			hand = HAND_TWOPAIR
			self.score = (hand, ordered_groups[0][0], ordered_groups[1][0], ordered_groups[2][0])
		elif ordered_groups[0][1] == 2:
			hand = HAND_PAIR
			self.score = (hand, ordered_groups[0][0], ordered_groups[1][0], ordered_groups[2][0], ordered_groups[3][0])
		else:
			hand = HAND_HIGH
			self.score = (hand, ordered_groups[0][0], ordered_groups[1][0], 
			ordered_groups[2][0], ordered_groups[3][0], ordered_groups[4][0])

	def calc_score(self):
		self.make_groups()
		self.make_seq()
		self.check_flush()

		self.determine_hand()

def set_places(results):
	place = 1
	prev = None
	for row in results:
		if prev is None or row[1] == prev:
			row[-1] = place
		else:
			place += 1
			row[-1] = place
		prev = row[1]

def score_sort(a, b): return cmp(a.score, b.score)

def find_best_hand(h, common):
	all_cards = h + common
	ms = []
	for combo in make_combinations(all_cards, 5):
		m = HandMeta(combo)
		m.calc_score()
		ms.append(m)
	ms.sort(score_sort)
	return ms[-1]

def eval_hands(hands, common):
	metas = {}
	for id, h in hands:
		metas[id] = find_best_hand(h, common)
	ids = metas.keys()
	ids.sort(lambda a, b: cmp(metas[a].score, metas[b].score))
	ids.reverse()
	results = [[id, metas[id].score, metas[id].cards, None] for id in ids]
	set_places(results)
	return results

def high_card(cards):
	cards = cards[:]
	cards.sort(cmp=card_compare, key=lambda k: k[1], reverse=True)
	winners = [cards[0]]
	winning_card = card(cards[0][1])
	for ind, c in cards[1:]:
		if card(c) == winning_card:
			winners.append((ind, c))
		else:
			break
	if len(winners) > 1:
		winners.sort(cmp=suit_compare, key=lambda k: k[1], reverse=True)

	return winners[0]
