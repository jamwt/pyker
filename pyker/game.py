import time
from itertools import dropwhile, chain

from pyker.deck import Deck
from pyker.pot import Pot
from pyker.util import *
from pyker.errors import GameError
from pyker.eval import eval_hands, high_card

def generate_blinds(start, cap):
	smb = start
	def dbl(v): 
		if v > cap:
			raise StopIteration
		return v, v *2

	for x in range(4):
		yield dbl(smb)
		smb += start
	smb -= start

	mult = 2
	while True:
		for x in range(2):
			smb += start * mult
			yield dbl(smb)
		mult *= 2

def round_rotation(dealer, small_blind, big_blind, active_players):
	if small_blind == None:
		# starting afresh.. new game!
		new_dealer = dealer
		if len(active_players) == 2:
			new_small_blind = dealer
			new_big_blind = next_extant_player(dealer, active_players)
		else:
			new_small_blind = next_extant_player(dealer, active_players)
			new_big_blind = next_extant_player(new_small_blind, active_players)

	else:
		new_big_blind = next_extant_player(big_blind, active_players)
		# Heads-up
		if len(active_players) == 2:
			ap = active_players[:]
			ap.remove(new_big_blind)
			new_small_blind = ap[0]
			if dealer not in active_players:
				new_dealer = next_extant_player(dealer, active_players)
			else:
				new_dealer = new_small_blind
		else:
			new_small_blind = next_extant_player(small_blind, active_players)
			if new_small_blind == new_big_blind:
				new_small_blind = new_big_blind - 1 # does not exist
				if new_small_blind == -1: # wrap...
					new_small_blind = Game.NUM_PLAYERS - 1
			new_dealer = next_extant_player(dealer, active_players)
			if new_dealer in (new_small_blind, new_big_blind):
				new_dealer = next_extant_player(new_small_blind, active_players, last=True)
	return new_dealer, new_small_blind, new_big_blind

class Game:
	NUM_PLAYERS = 8
	def __init__(self, blinds_start, blinds_cap, blinds_timer, stack_start):
		self.state = {} # extra game state info.. server tracked
		self.action = None
		self.game_ended = False
		self.blinds_start = blinds_start
		self.blinds_cap = blinds_cap
		self.blinds_timer = blinds_timer
		self.blinds_sequence = generate_blinds(self.blinds_start, self.blinds_cap)
		self.starttime = None
		self.stack_start = stack_start
		self.players = {}
		for x in xrange(1, self.NUM_PLAYERS + 1):
			self.players[x] = None
		self.deck = Deck()
		self.dealer = None
		self.small_blind = None
		self.big_blind = None
		self.sb_amt = 0
		self.bb_amt = 0
		self.started = False
		self.community = []
		self.minimum_bet = self.blinds_start
		self.pot = Pot()
		self.hand_over = False
		self.payments = None
		self.show = []
		self.show_all = False
		self.places = []
		self.payouts = []

	def winners(self):
		s = set()
		for p in self.payouts:
			for w, amt in p:
				s.add(w)
		return s
	winners = property(winners)

	def add_player(self, player, position):
		player.sit_in()
		if position <= 0 or position > self.NUM_PLAYERS:
			player.stand_up()
			raise GameError, "Invalid seating position"

		if self.players[position]:
			player.stand_up()
			raise GameError, "A player is already sitting in that position"
		self.players[position] = player

	def _get_active_players(self):
		return dict((pos, p) for pos, p in self.players.iteritems() if p and p.sitting)
	active_players = property(_get_active_players)

	def _get_active_players_o(self):
		return [v for k, v in sorted(self.active_players.items(), key=lambda x: x[0])]
	active_players_o = property(_get_active_players_o)

	def _get_in_players(self):
		def from_dealer_sort(packed):
			x, _p = packed
			amt = x - self.dealer
			if amt <= 0:
				amt += self.NUM_PLAYERS
			return amt
		return sorted([(pos, p) for pos, p in self.active_players.iteritems() if p.playing],
		key=from_dealer_sort)

	in_players = property(_get_in_players)

	def ip_around(self, all=False):
		seen = set()
		while True:
			for pos, p in self.in_players:
				if all or p.purse > 0 or pos in seen:
					seen.add(pos)
					yield pos, p

	def _get_hands(self):
		return dict((pos, p.hand) for pos, p in self.in_players)
	hands = property(_get_hands)

	def call_around(self):
		rab = self.ip_around(all=True)
		out = rab.next()
		while out != self.called:
			out = rab.next()
		for x in xrange(len(self.in_players)):
			yield out
			out = rab.next()

	def evaluate(self):
		'''Return the payouts, shows, etc.
		'''
		if not self.hand_over:
			raise GameError, "hand is not over yet"

		self.show = []
		# fold to this player
		if len(self.in_players) == 1:
			winner_pos, winner_obj = self.in_players[0]
			tot = self.pot.total
			self.payouts = [[(winner_pos, tot)]]
		else:
			raw_evals = eval_hands(
			[(pos, p.hand) for pos, p in self.in_players], self.community)
			self.payouts = self.pot.payout(raw_evals, self.dealer)
			hand_key = dict((pos, (hand, cards)) for pos, hand, cards, place in raw_evals)

			shot_at_pot = {}
			best_hands = {}
			for amt, players in self.pot.pots:
				best_hands[amt] = ()
				for p in players:
					shot_at_pot.setdefault(p, []).append(amt)
			
			show = []
			for pos, p in self.call_around():
				if self.show_all:
					show.append((pos, hand_key[pos]))
				else:
					show_it = False
					for amt in shot_at_pot[pos]:
						hand_score, cards = hand_key[pos]
						if hand_score > best_hands[amt]:
							show_it = True
							best_hands[amt] = hand_score
					if show_it:
						show.append((pos, hand_key[pos]))
					else:
						show.append((pos, None))
						p.fold()

			self.show = show

	def make_payments(self):
		if self.payment_made:
			raise GameError, "payment already made"
		self.payment_made = True
		for pot in self.payouts:
			for pos, amt in pot:
				self.players[pos].fund(amt)
		self.payouts = []

	def find_first_dealer(self):
		self.show_all = True
		self.deck.collect_shuffle()
		self.deck.deal(self.active_players_o, 1)
		highest = high_card([(pos, p.hand[0]) for pos, p in self.active_players.iteritems()])
		self.dealer = highest[0]

	def start(self):
		# Find first dealer
		if len(self.active_players) == 0:
			raise GameError, "no players at table"
		if len(self.active_players) == 1:
			raise GameError, "only one player at table"
		self.started = True
		self.init_num_players = len(self.active_players)
		for p in self.active_players.itervalues():
			p.fund(self.stack_start)
		self.find_first_dealer()
		self.starttime = time.time()
		self.advance_blinds()

	def advance_blinds(self):
		self.sb_amt, self.bb_amt = self.blinds_sequence.next()

	def _get_pot_amount(self):
		return sum(self.pot.itervalues())
	pot_amount = property(_get_pot_amount)

	def clear_hands(self):
		for p in self.active_players.itervalues():
			p.discard()
			p.playing = True

	def start_hand(self):
		self.pot = Pot()
		self.show = []
		self.dealer, self.small_blind, self.big_blind = \
		round_rotation(self.dealer, self.small_blind, self.big_blind,
		self.active_players.keys())
		self.clear_hands()

		self.community = []
		self.deck.collect_shuffle()
		self.first_round_done = False
		self.hand_over = False
		self.show_all = False
		self.payment_made = False

	def start_betting_round(self):
		self.dead_pot = False
		self.roundabout = self.ip_around()
		self.pot.new_round()
		self.action = None
		self.bet_made = False
		if not self.first_round_done:
			self.first_round_done = True
			# dealer bets first in heads-up play
			if len(self.active_players) == 2: 
				self.roundabout.next()
			pos, p = self.roundabout.next()
			self.bet(pos, self.sb_amt)
			pos, p = self.roundabout.next()
			self.bet(pos, self.bb_amt)
		self.pot.set_minimum(self.bb_amt)
		self.taken_turn = set()
		self.action = self.roundabout.next()

	def deal_pockets(self):
		self.deck.deal(self.active_players_o, 2)
		# network.new_hand

	def deal_community(self):
		if not self.community:
			for x in xrange(3):
				self.community.append(self.deck.get_card())
		else:
			self.community.append(self.deck.get_card())

	def bet(self, pos, amt):
		player = self.players[pos]
		if self.dead_pot:
			raise GameError, "Player '%s': cannot bet out of turn!" % player.nick

		if self.action and self.action[0] != pos:
			raise GameError, "Player '%s': cannot bet out of turn!" % player.nick

		if amt >= 0:
			amt = min(amt, player.purse)
			player.deduct(amt)
			all_in = player.purse == 0 and True or False
			if self.bet_made and amt < self.pot.deficit(pos) and not all_in:
				raise GameError, "Player '%s': you must bet at least $%d to call" % (player.nick, self.pot.deficit(pos))
			if amt > 0:
				if not all_in and amt > self.pot.deficit(pos) and len([p for _pos, p in self.in_players if p.purse > 0]) < 2:
					raise GameError, "Player '%s': all other players are all in; either call $%d or fold" % (player.nick, self.pot.deficit(pos))

				try:
					typ = self.pot.bet(pos, amt, all_in=all_in)
				except GameError:
					player.fund(amt) # give the player back his money!
					raise
				if not self.bet_made:
					typ = Pot.BET_BET
				self.bet_made = True
			else:
				typ = Pot.BET_CHECK
		else:
			player.fold()
			typ = Pot.BET_FOLD

		if self.action:
			self.taken_turn.add(pos)
			self.action = self.roundabout.next()
			if len(self.in_players) == 1 or (self.action[0] in self.taken_turn and (self.pot.deficit(self.action[0]) == 0 
			or not self.bet_made)):
				# end of the betting round
				self.called = self.action
				self.action = None
				self.pot.end_round()
				self.dead_pot = True
				self.check_for_winners()
		return typ

	def check_for_winners(self):
		'''Called after a betting round.. is it time to showdown?
		'''
		 # everyone folded or all cards are dealt
		if len(self.in_players) == 1 or len(self.community) == 5:
			self.hand_over = True
		 # everyone all-in (possibly except one player)
		if len(self.in_players) > 1 and len([p for pos, p in self.in_players if p.purse > 0]) <= 1:
			self.show_all = True

	def finish_hand(self):
		for pos, p in self.in_players:
			if p.purse == 0:
				p.discard()
				p.sitting = False
				p.playing = False
				self.places.append((
					self.init_num_players - len(self.places), # places
					pos,
					p.nick,
					))
		if len(self.active_players) == 1:
			self.game_ended = True
			pos, p = self.active_players.items()[0]
			p.discard()
			self.places.append((
				self.init_num_players - len(self.places), # places
				pos,
				p.nick,
				))
