from pyker.errors import GameError
from pyker.util import *

class Pot:
	def __init__(self):
		self._wagers = {}
		self.bet_amount = 0
		self.allins = set()
		self.allin_players = set()
		self.round = {}

	def end_round(self):
		for key, val in self.round.iteritems():
			if key in self._wagers:
				self._wagers[key] += val
			else:
				self._wagers[key] = val
		self.round = {}

	def new_round(self, minimum=0):
		self.bet_amount = minimum
		self.round = {}

	def set_minimum(self, amt):
		self.bet_amount = amt

	BET_CALL, BET_RAISE, BET_FOLD, BET_CHECK, BET_BET = range(5)
	def bet(self, pos, amt, all_in=False):
		btype = self.BET_CALL
		paid = self.round.get(pos, 0) + amt
		if not all_in and paid < self.bet_amount:
			raise GameError, "total bet must be at least $%d" % self.bet_amount

		if paid > self.bet_amount:
			if not all_in and paid < self.bet_amount * 2:
				raise GameError, "raise must be equal to or greater than the last raise/bet"

			self.bet_amount = paid
			btype = self.BET_RAISE

		if all_in:
			if pos in self._wagers:
				self._wagers[pos] += paid
			else:
				self._wagers[pos] = paid
			if pos in self.round:
				del self.round[pos]
			self.allins.add(self._wagers[pos])
			self.allin_players.add(pos)
		else:
			self.round[pos] = paid
		return btype

	def _get_total(self):
		return sum(p[0] for p in self.pots)
	total = property(_get_total)

	def _get_alltotal(self):
		return sum(p[0] for p in self.pots) + sum(self.round.values())
	alltotal = property(_get_alltotal)

	def deficit(self, pos):
		if pos in self.allin_players:
			return 0
		return self.bet_amount - self.round.get(pos, 0)

	def _get_pots(self):
		if not self._wagers:
			return []

		pot_items = self._wagers.items()
		pot_items.sort(key=lambda x: x[1])
		pot_bets = self.allins.copy()
		pot_bets.add(pot_items[-1][1]) # update with the high bet
		pockets = self._wagers.copy()
		pots = []
		for bet_level in sorted(list(pot_bets)):
			eligible = []
			conts = []
			for pos, amount in pot_items:
				if amount >= bet_level:
					eligible.append(pos)
					conts.append(min(bet_level, pockets[pos]))
			adj_level = min(conts)
			value = 0
			for pos, amount in pot_items:
				actual_cont = min(adj_level, pockets[pos])
				value += actual_cont
				pockets[pos] -= actual_cont

			pots.append((value, eligible))
		assert sum(pockets.values()) == 0 # all money should have been distributed

		return pots
	pots = property(_get_pots)

	def payout(self, ranking_results, dealer):
		payouts = []
		def dealer_sort_key(pos):
			key = dealer - pos
			if key < 0:
				key += 100
			return key

		for total, players in self.pots:
			win_place = None
			winners = []
			for pos, hand, cards, place in ranking_results:
				if pos in players:
					if not win_place:
						win_place = place
					elif place != win_place:
						break
					winners.append(pos)
				elif win_place:
					break
			winnings = make_split_amounts(total, len(winners))
			winners.sort(key=dealer_sort_key)
			pot_wins = zip(winners, winnings)
			payouts.append(pot_wins)

		return payouts
