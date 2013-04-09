from pyker import *
import py.test

from pyker.deck import Deck
from pyker.pot import Pot


class UtilTestDeck(Deck):
	def get_card(self):
		if hasattr(self, '_testcards') and self._testcards:
			return self._testcards.pop(0)
		return Deck.get_card(self)

	def testing_add_cards(self, cards):
		if not hasattr(self, '_testcards'):
			self._testcards = cards[:]
		else:
			self._testcards.extend(cards)

class TestSetup:
	def test_create_game(self):
		self.game = Game(25, 800, 12, 1500)

	def test_create_players(self):
		self.player_one = Player("Jamie")
		self.player_two = Player("Dave")
		
	def test_add_players(self):
		self.game.add_player(self.player_one, 1)
		self.game.add_player(self.player_two, 7)
		assert len(self.game.active_players) == 2

	def test_readd_player(self):
		py.test.raises(GameError, self.game.add_player, 
		self.player_one, 2) # already in the game
		assert len(self.game.active_players) == 2

	def test_slot_taken(self):
		new_player = Player("Joey")
		py.test.raises(GameError, self.game.add_player, 
		new_player, 1) # slot_taken
		assert len(self.game.active_players) == 2
	
class TestStart:
	def setup_class(self):
		self.game = Game(25, 800, 12, 1500)
		self.game.deck = UtilTestDeck()

	def test_start_empty(self):
		py.test.raises(GameError, self.game.start)

	def test_start(self):
		self.player_one = Player("Jamie")
		self.player_two = Player("Dave")
		self.game.add_player(self.player_one, 1)
		self.game.add_player(self.player_two, 7)
		self.game.deck.testing_add_cards(["2S", "JD"])
		self.game.start()

	def test_initial_dealer_draw(self):
		assert len(self.game.hands) == 2
		assert self.game.dealer == 7

class TestGame:
	def setup_class(self):
		self.game = Game(25, 800, 12, 1500)
		self.game.deck = UtilTestDeck()
		self.game.blinds_sequence = iter([(25, 50), (50, 100), (100, 200), (200, 400), (300, 600), (400, 800)])
		self.p_jamie = Player("Jamie")
		self.p_dave = Player("Dave")
		self.p_brian = Player("Brian")
		self.p_chris = Player("Chris")
		self.game.add_player(self.p_jamie, 1)
		self.game.add_player(self.p_dave, 2)
		self.game.add_player(self.p_brian, 3)
		self.game.add_player(self.p_chris, 4)
		self.game.deck.testing_add_cards(["2S", "7S", "9D", "6C"])
		self.game.start()

	def test_starting_pos(self):
		assert self.game.dealer == 3

	def test_hand_1(self):
		game = self.game
		game.start_hand()
		game.deck.testing_add_cards(["KS", "2C", "KD", "6C",
									 "8C", "3C", "9D", "6D",
										  ])
		game.deal_pockets()
		assert self.p_jamie.hand == ["KS", "8C"]
		assert self.p_dave.hand == ["2C", "3C"]
		assert self.p_brian.hand == ["KD", "9D"]
		assert self.p_chris.hand == ["6C", "6D"]

		assert game.dealer == 3
		assert game.small_blind == 4
		assert game.big_blind == 1
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (2, self.p_dave)

		assert game.bet(2, -1) == Pot.BET_FOLD # dave folds
		assert game.bet(3, 50) == Pot.BET_CALL # brian calls
		assert game.bet(4, 25) == Pot.BET_CALL # chris calls
		assert game.pot.deficit(4) == 0
		assert game.action == (1, self.p_jamie)
		assert game.pot.deficit(1) == 0
		assert game.bet(1, 0) == Pot.BET_CHECK
		assert game.action == None
		assert game.pot.pots == [(150, [1, 3, 4])]

		assert self.p_jamie.purse == 1450
		assert self.p_dave.purse == 1500
		assert self.p_brian.purse == 1450
		assert self.p_chris.purse == 1450
		
		game.deck.testing_add_cards(["QS", "TD", "2H"])
		game.deal_community()
		assert game.community  == ["QS", "TD", "2H"]

		game.start_betting_round()
		assert game.action == (4, self.p_chris)
		assert game.bet(4, 0) == Pot.BET_CHECK
		assert game.bet(1, 200) == Pot.BET_BET
		assert game.bet(3, 200) == Pot.BET_CALL
		assert game.bet(4, -1) == Pot.BET_FOLD
		assert game.action == None
		assert game.pot.pots == [(550, [1, 3])]

		assert self.p_jamie.purse == 1250
		assert self.p_dave.purse == 1500
		assert self.p_brian.purse == 1250
		assert self.p_chris.purse == 1450

		game.deck.testing_add_cards(["5D"])
		game.deal_community()
		assert game.community  == ["QS", "TD", "2H", "5D"]

		game.start_betting_round()
		assert game.action == (1, self.p_jamie)
		assert game.bet(1, 0) == Pot.BET_CHECK
		assert game.bet(3, 0) == Pot.BET_CHECK
		assert game.action == None

		game.deck.testing_add_cards(["2S"])
		game.deal_community()
		assert game.community  == ["QS", "TD", "2H", "5D", "2S"]

		game.start_betting_round()
		assert game.bet(1, 300) == Pot.BET_BET
		assert game.bet(3, -1) == Pot.BET_FOLD
		assert game.action == None

		assert game.hand_over == True
		assert game.show_all == False

		game.evaluate()
		assert game.payouts == [[(1, 850)]]
		assert game.show == []

		game.make_payments()
		assert self.p_jamie.purse == 1800
		assert self.p_dave.purse == 1500
		assert self.p_brian.purse == 1250
		assert self.p_chris.purse == 1450

		game.finish_hand()
		assert len(game.active_players) == 4

	def test_hand_2(self):
		game = self.game
		game.start_hand()
		game.deck.testing_add_cards(["JC", "9S", "5H", "AC",
									 "2D", "KS", "6C", "JS",
										  ])
		game.deal_pockets()
		assert self.p_jamie.hand == ["JC", "2D"]
		assert self.p_dave.hand == ["9S", "KS"]
		assert self.p_brian.hand == ["5H", "6C"]
		assert self.p_chris.hand == ["AC", "JS"]

		assert game.dealer == 4
		assert game.small_blind == 1
		assert game.big_blind == 2
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (3, self.p_brian)

		assert game.bet(3, -1) == Pot.BET_FOLD # brian folds
		assert game.bet(4, 150) == Pot.BET_RAISE # chris raises to 150
		assert game.bet(1, -1) == Pot.BET_FOLD # jamie folds
		assert game.bet(2, 100) == Pot.BET_CALL # dave calls 150 (+100)
		assert game.action == None
		assert game.pot.pots == [(325, [2, 4])]

		assert self.p_jamie.purse == 1775
		assert self.p_dave.purse == 1350
		assert self.p_brian.purse == 1250
		assert self.p_chris.purse == 1300
		
		game.deck.testing_add_cards(["4D", "3S", "3D"])
		game.deal_community()
		assert game.community  == ["4D", "3S", "3D"]

		game.start_betting_round()
		assert game.action == (2, self.p_dave)
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.bet(4, 250) == Pot.BET_BET
		assert game.bet(2, -1) == Pot.BET_FOLD
		assert game.action == None

		assert game.hand_over == True
		assert game.show_all == False

		game.evaluate()
		assert game.payouts == [[(4, 575)]]
		assert game.show == []

		game.make_payments()
		assert self.p_jamie.purse == 1775
		assert self.p_dave.purse == 1350
		assert self.p_brian.purse == 1250
		assert self.p_chris.purse == 1625

		game.finish_hand()
		assert len(game.active_players) == 4
		assert game.places == []

	def test_hand_3(self):
		game = self.game
		game.start_hand()
		game.deck.testing_add_cards(["3D", "AD", "4S", "7S",
									 "KD", "KH", "8H", "2H",
										  ])
		game.deal_pockets()

		assert game.dealer == 1
		assert game.small_blind == 2
		assert game.big_blind == 3
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (4, self.p_chris)

		assert game.bet(4, -1) == Pot.BET_FOLD # chris folds
		assert game.bet(1, -1) == Pot.BET_FOLD # jamie folds
		assert game.bet(2, 25) == Pot.BET_CALL # dave calls 50 (+25)
		assert game.bet(3, 0) == Pot.BET_CHECK # brian checks
		assert game.action == None
		assert game.pot.pots == [(100, [2, 3])]

		assert self.p_jamie.purse == 1775
		assert self.p_dave.purse == 1300
		assert self.p_brian.purse == 1200
		assert self.p_chris.purse == 1625
		
		game.deck.testing_add_cards(["6S", "9C", "QH"])
		game.deal_community()
		assert game.community  == ["6S", "9C", "QH"]

		game.start_betting_round()
		assert game.action == (2, self.p_dave)
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.bet(3, 0) == Pot.BET_CHECK
		assert game.action == None

		game.deck.testing_add_cards(["TS"])
		game.deal_community()
		assert game.community  == ["6S", "9C", "QH", "TS"]

		game.start_betting_round()
		assert game.action == (2, self.p_dave)
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.bet(3, 0) == Pot.BET_CHECK
		assert game.action == None

		game.deck.testing_add_cards(["AH"])
		game.deal_community()
		assert game.community  == ["6S", "9C", "QH", "TS", "AH"]

		game.start_betting_round()
		assert game.action == (2, self.p_dave)
		assert game.bet(2, 150) == Pot.BET_BET
		assert game.bet(3, -1) == Pot.BET_FOLD
		assert game.action == None

		assert game.hand_over == True
		assert game.show_all == False

		game.evaluate()
		assert game.payouts == [[(2, 250)]]
		assert game.show == []

		game.make_payments()
		assert self.p_jamie.purse == 1775
		assert self.p_dave.purse == 1400
		assert self.p_brian.purse == 1200
		assert self.p_chris.purse == 1625

		game.finish_hand()
		assert len(game.active_players) == 4

	def show_strings(self, game):
		r = []
		for pos, info in game.show:
			if info:
				r.append((pos, get_hand_phrase(info[0])))
			else:
				r.append((pos, '<FOLD>'))
		return r

	def test_hand_4(self):
		game = self.game
		game.advance_blinds()
		game.start_hand()
		game.deck.testing_add_cards(["3D", "AD", "4S", "7S",
									 "KD", "KH", "8H", "2H",
										  ])
		game.deal_pockets()

		assert game.dealer == 2
		assert game.small_blind == 3
		assert game.big_blind == 4
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (1, self.p_jamie)

		assert game.bet(1, -1) == Pot.BET_FOLD # jamie folds
		assert game.bet(2, -1) == Pot.BET_FOLD # dave folds
		assert game.bet(3, 250) == Pot.BET_RAISE # brian raises to $300 (+250)
		assert game.bet(4, 200) == Pot.BET_CALL  # chris calls 300
		assert game.action == None
		assert game.pot.pots == [(600, [3, 4])]

		assert self.p_jamie.purse == 1775
		assert self.p_dave.purse == 1400
		assert self.p_brian.purse == 900
		assert self.p_chris.purse == 1325
		
		game.deck.testing_add_cards(["2D", "4S", "6D"])
		game.deal_community()
		assert game.community  == ["2D", "4S", "6D"]

		game.start_betting_round()
		assert game.action == (3, self.p_brian)
		assert game.bet(3, 400) == Pot.BET_BET
		assert game.bet(4, -1) == Pot.BET_FOLD
		assert game.action == None

		assert game.hand_over == True
		assert game.show_all == False

		game.evaluate()
		assert game.payouts == [[(3, 1000)]]
		assert game.show == []

		game.make_payments()
		assert self.p_jamie.purse == 1775
		assert self.p_dave.purse == 1400
		assert self.p_brian.purse == 1500
		assert self.p_chris.purse == 1325

		game.finish_hand()
		assert len(game.active_players) == 4

	def test_hand_5(self):
		game = self.game
		game.start_hand()
		game.deck.testing_add_cards(["8D", "KS", "7C", "2S",
									 "6D", "TC", "3S", "AC",
										  ])
		game.deal_pockets()

		assert game.dealer == 3
		assert game.small_blind == 4
		assert game.big_blind == 1
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (2, self.p_dave)

		assert game.bet(2, 100) == Pot.BET_CALL # dave calls
		assert game.bet(3, -1) == Pot.BET_FOLD # brian folds
		assert game.bet(4, 50) == Pot.BET_CALL # chris calls $100 (+50)
		assert game.bet(1, 0) == Pot.BET_CHECK  # chris calls 300
		assert game.action == None
		assert game.pot.pots == [(300, [1, 2, 4])]

		assert self.p_jamie.purse == 1675
		assert self.p_dave.purse == 1300
		assert self.p_brian.purse == 1500
		assert self.p_chris.purse == 1225
		
		game.deck.testing_add_cards(["4H", "QS", "JC"])
		game.deal_community()
		assert game.community  == ["4H", "QS", "JC"]

		game.start_betting_round()
		assert game.action == (4, self.p_chris)
		assert game.bet(4, 0) == Pot.BET_CHECK
		assert game.bet(1, 0) == Pot.BET_CHECK
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.action == None

		game.deck.testing_add_cards(["7H"])
		game.deal_community()
		assert game.community  == ["4H", "QS", "JC", "7H"]

		game.start_betting_round()
		assert game.action == (4, self.p_chris)
		assert game.bet(4, 0) == Pot.BET_CHECK
		assert game.bet(1, 0) == Pot.BET_CHECK
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.action == None

		game.deck.testing_add_cards(["AS"])
		game.deal_community()
		assert game.community  == ["4H", "QS", "JC", "7H", "AS"]

		game.start_betting_round()
		assert game.action == (4, self.p_chris)
		assert game.bet(4, 400) == Pot.BET_BET
		assert game.bet(1, -1) == Pot.BET_FOLD
		assert game.bet(2, 800) == Pot.BET_RAISE
		assert game.bet(4, 825) == Pot.BET_RAISE # all-in
		assert game.bet(2, 425) == Pot.BET_CALL 
		assert self.p_dave.purse == 75
		assert self.p_chris.purse == 0
		assert game.action == None

		assert game.hand_over == True
		assert game.show_all == True

		game.evaluate()
		assert game.payouts == [[(2, 2750)]]
		assert self.show_strings(game) == [
		(4, "pair of aces, queen kicker"),
		(2, "straight to the ace"),
		]

		game.make_payments()
		assert self.p_jamie.purse == 1675
		assert self.p_dave.purse == 2825
		assert self.p_brian.purse == 1500
		assert self.p_chris.purse == 0

		game.finish_hand()
		assert len(game.active_players) == 3
		assert game.places == [(4, 4, 'Chris')]

	def test_hand_6(self):
		game = self.game
		game.advance_blinds()
		game.start_hand()
		game.deck.testing_add_cards(["3S", "9H", "6D",
									 "2S", "4D", "2D",
										  ])
		game.deal_pockets()

		assert self.p_jamie.hand == ["3S", "2S"]
		assert self.p_dave.hand == ["9H", "4D"]
		assert self.p_brian.hand == ["6D", "2D"]

		assert game.dealer == 3
		assert game.small_blind == 1
		assert game.big_blind == 2
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (3, self.p_brian)

		assert game.bet(3, -1) == Pot.BET_FOLD # brian folds
		assert game.bet(1, 100) == Pot.BET_CALL # jamie calls $200 (+100)
		assert game.bet(2, 0) == Pot.BET_CHECK # dave checks
		assert game.action == None
		assert game.pot.pots == [(400, [1, 2])]

		assert self.p_jamie.purse == 1475
		assert self.p_dave.purse == 2625
		assert self.p_brian.purse == 1500
		
		game.deck.testing_add_cards(["JC", "KS", "AS"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(1, 0) == Pot.BET_CHECK
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.action == None

		game.deck.testing_add_cards(["7C"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(1, 0) == Pot.BET_CHECK
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.action == None

		game.deck.testing_add_cards(["6H"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(1, 0) == Pot.BET_CHECK
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.action == None

		assert game.hand_over == True
		assert game.show_all == False

		game.evaluate()
		assert game.payouts == [[(2, 400)]]
		assert self.show_strings(game) == [
		(1, "ace high"),
		(2, "ace high"),
		]

		game.make_payments()
		assert self.p_jamie.purse == 1475
		assert self.p_dave.purse == 3025
		assert self.p_brian.purse == 1500

		game.finish_hand()
		assert len(game.active_players) == 3

	def test_hand_7(self):
		game = self.game
		game.start_hand()
		game.deck.testing_add_cards(["AD", "9H", "AH",
									 "6D", "8D", "QS",
										  ])
		game.deal_pockets()

		assert game.dealer == 1
		assert game.small_blind == 2
		assert game.big_blind == 3
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (1, self.p_jamie)

		assert game.bet(1, 200) == Pot.BET_CALL # jamie calls $200
		assert game.bet(2, 100) == Pot.BET_CALL # dave calls $200 (+100)
		assert game.bet(3, 0) == Pot.BET_CHECK # brian checks
		assert game.action == None
		assert game.pot.pots == [(600, [1, 2, 3])]

		assert self.p_jamie.purse == 1275
		assert self.p_dave.purse == 2825
		assert self.p_brian.purse == 1300
		
		game.deck.testing_add_cards(["9S", "4C", "KC"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(2, 800) == Pot.BET_BET
		assert game.bet(3, -1) == Pot.BET_FOLD
		assert game.bet(1, -1) == Pot.BET_FOLD
		assert game.action == None

		assert game.hand_over == True
		assert game.show_all == False

		game.evaluate()
		assert game.payouts == [[(2, 1400)]]

		game.make_payments()
		assert self.p_jamie.purse == 1275
		assert self.p_dave.purse == 3425
		assert self.p_brian.purse == 1300

		game.finish_hand()
		assert len(game.active_players) == 3

	def test_hand_8(self):
		game = self.game
		game.start_hand()
		game.deck.testing_add_cards(["2H", "6H", "AD",
									 "5H", "AC", "3S",
										  ])
		game.deal_pockets()

		assert game.dealer == 2
		assert game.small_blind == 3
		assert game.big_blind == 1
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (2, self.p_dave)

		assert game.bet(2, 200) == Pot.BET_CALL # dave calls $200
		assert game.bet(3, 100) == Pot.BET_CALL # brian calls $200 (+100)
		assert game.bet(1, 0) == Pot.BET_CHECK # jamie checks
		assert game.action == None
		assert game.pot.pots == [(600, [1, 2, 3])]

		assert self.p_jamie.purse == 1075
		assert self.p_dave.purse == 3225
		assert self.p_brian.purse == 1100
		
		game.deck.testing_add_cards(["JC", "3D", "QS"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(3, 1100) == Pot.BET_BET
		assert game.bet(1, -1) == Pot.BET_FOLD
		assert game.bet(2, -1) == Pot.BET_FOLD
		assert game.action == None

		assert game.hand_over == True
		assert game.show_all == False

		game.evaluate()
		assert game.payouts == [[(3, 1700)]]

		game.make_payments()
		assert self.p_jamie.purse == 1075
		assert self.p_dave.purse == 3225
		assert self.p_brian.purse == 1700

		game.finish_hand()
		assert len(game.active_players) == 3

	def test_hand_9(self):
		game = self.game
		game.advance_blinds()
		game.start_hand()
		game.deck.testing_add_cards(["7D", "JD", "QH",
									 "AD", "KS", "3D",
										  ])
		game.deal_pockets()

		assert game.dealer == 3
		assert game.small_blind == 1
		assert game.big_blind == 2
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (3, self.p_brian)

		assert game.bet(3, 400) == Pot.BET_CALL # brian calls $400
		assert game.bet(1, 875) == Pot.BET_RAISE # all-in.. 
		assert game.bet(2, 675) == Pot.BET_CALL # jamie checks
		assert game.bet(3, 675) == Pot.BET_CALL # jamie checks
		assert game.action == None
		assert game.pot.pots == [(3225, [1, 2, 3])]

		assert self.p_jamie.purse == 0
		assert self.p_dave.purse == 2150
		assert self.p_brian.purse == 625
		assert game.show_all == False
		
		game.deck.testing_add_cards(["9D", "4D", "6H"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.bet(3, 0) == Pot.BET_CHECK
		assert game.action == None

		game.deck.testing_add_cards(["JH"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.bet(3, 0) == Pot.BET_CHECK
		assert game.action == None

		game.deck.testing_add_cards(["5D"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.bet(3, 0) == Pot.BET_CHECK
		assert game.action == None

		assert game.hand_over == True
		assert game.show_all == False

		game.evaluate()
		assert game.payouts == [[(1, 3225)]]
		assert self.show_strings(game) == [
		(2, "pair of jacks, king kicker"),
		(3, "<FOLD>"),
		(1, "ace high flush"),
		]

		game.make_payments()
		assert self.p_jamie.purse == 3225
		assert self.p_dave.purse == 2150
		assert self.p_brian.purse == 625

		game.finish_hand()
		assert len(game.active_players) == 3

	def test_hand_10(self):
		game = self.game
		game.start_hand()
		game.deck.testing_add_cards(["7S", "4C", "4S",
									 "KC", "6C", "QC",
										  ])
		game.deal_pockets()

		assert game.dealer == 1
		assert game.small_blind == 2
		assert game.big_blind == 3
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (1, self.p_jamie)

		assert game.bet(1, 800) == Pot.BET_RAISE # jamie raises to $800
		assert game.bet(2, -1) == Pot.BET_FOLD  # dave folds
		assert game.bet(3, 225) == Pot.BET_CALL # call -- all in
		assert game.action == None
		assert game.pot.pots == [(1450, [3, 1]), (175, [1])]
		assert game.pot.total == 1625
		assert game.show_all == True
		assert game.hand_over == False

		game.deck.testing_add_cards(["2H", "AH", "KS", "JC", "5C"])
		game.deal_community()
		assert len(game.community) == 3
		game.deal_community()
		assert len(game.community) == 4
		game.deal_community()
		assert len(game.community) == 5
		game.check_for_winners()

		assert game.hand_over == True

		game.evaluate()
		assert game.payouts == [[(1, 1450)], [(1, 175)]]
		assert self.show_strings(game) == [
		(1, "pair of kings, ace kicker"),
		(3, "ace high"),
		]

		game.make_payments()
		assert self.p_jamie.purse == 4050
		assert self.p_dave.purse == 1950
		assert self.p_brian.purse == 0

		game.finish_hand()
		assert len(game.active_players) == 2
		assert game.places == [(4, 4, 'Chris'), (3, 3, 'Brian')]

	def test_hand_11(self):
		game = self.game
		game.advance_blinds()
		game.start_hand()
		game.deck.testing_add_cards(["5D", "TS",
									 "6C", "7H"
										  ])
		game.deal_pockets()

		assert game.dealer == 2
		assert game.small_blind == 2
		assert game.big_blind == 1
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (2, self.p_dave)

		assert game.bet(2, 900) == Pot.BET_RAISE # dave raises to $1200
		assert game.bet(1, -1) == Pot.BET_FOLD  # jamie folds
		assert game.action == None

		assert game.show_all == False
		assert game.hand_over == True

		game.evaluate()
		assert game.payouts == [[(2, 1800)]]
		game.make_payments()
		assert self.p_jamie.purse == 3450
		assert self.p_dave.purse == 2550
		assert self.p_brian.purse == 0

		game.finish_hand()
		assert len(game.active_players) == 2

	def test_hand_12(self):
		game = self.game
		game.start_hand()
		game.deck.testing_add_cards(["4D", "AD",
									 "JC", "6C",
										  ])
		game.deal_pockets()

		assert game.dealer == 1
		assert game.small_blind == 1
		assert game.big_blind == 2
		assert game.pot.pots == []

		game.start_betting_round()
		assert game.action == (1, self.p_jamie)

		assert game.bet(1, 300) == Pot.BET_CALL # jamie calls $600
		assert game.bet(2, 0) == Pot.BET_CHECK  # dave checks
		assert game.action == None

		assert game.show_all == False
		assert game.hand_over == False

		game.deck.testing_add_cards(["JS", "3D", "9S"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.bet(1, 1200) == Pot.BET_BET
		assert game.bet(2, -1) == Pot.BET_FOLD
		assert game.action == None

		assert game.show_all == False
		assert game.hand_over == True

		game.evaluate()
		assert game.payouts == [[(1, 2400)]]
		game.make_payments()
		assert self.p_jamie.purse == 4050
		assert self.p_dave.purse == 1950

		game.finish_hand()
		assert len(game.active_players) == 2

	def test_hand_13(self):
		game = self.game
		game.start_hand()
		game.deck.testing_add_cards(["7C", "AS",
									 "2S", "9C"
										  ])
		game.deal_pockets()

		assert game.dealer == 2
		assert game.small_blind == 2
		assert game.big_blind == 1
		assert game.pot.pots == []

		game.start_betting_round()

		assert game.bet(2, 300) == Pot.BET_CALL # dave calls $600
		assert game.bet(1, 0) == Pot.BET_CHECK  # jamie checks
		assert game.action == None

		assert game.pot.total == 1200

		game.deck.testing_add_cards(["3C", "5C", "AH"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(1, 0) == Pot.BET_CHECK
		assert game.bet(2, 1350) == Pot.BET_BET # all-in
		assert game.bet(1, 1350) == Pot.BET_CALL
		assert game.action == None

		assert game.show_all == True
		assert game.hand_over == False

		game.deck.testing_add_cards(["3S", "AD"])
		game.deal_community()
		assert len(game.community) == 4
		game.deal_community()
		assert len(game.community) == 5
		print game.community
		game.check_for_winners()

		game.evaluate()
		assert game.payouts == [[(2, 3900)]]
		assert self.show_strings(game) == [
		(2, "full house, aces full of threes"),
		(1, "two pair of aces and threes"),
		]

		game.make_payments()
		assert self.p_jamie.purse == 2100
		assert self.p_dave.purse == 3900

		game.finish_hand()
		assert len(game.active_players) == 2

	def test_hand_14(self):
		game = self.game
		game.advance_blinds()
		game.start_hand()
		game.deck.testing_add_cards(["6S", "KD",
									 "7S", "5C",
										  ])
		game.deal_pockets()

		assert game.dealer == 1
		assert game.small_blind == 1
		assert game.big_blind == 2
		assert game.pot.pots == []

		game.start_betting_round()

		assert game.bet(1, 400) == Pot.BET_CALL # jamie calls $800
		assert game.bet(2, 0) == Pot.BET_CHECK  # dave checks
		assert game.action == None

		assert game.pot.total == 1600

		game.deck.testing_add_cards(["3D", "QD", "2S"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.bet(1, 0) == Pot.BET_CHECK
		assert game.action == None

		game.deck.testing_add_cards(["6D"])
		game.deal_community()

		game.start_betting_round()
		assert game.bet(2, 0) == Pot.BET_CHECK
		assert game.bet(1, 1300) == Pot.BET_BET # all-in
		assert game.bet(2, 1300) == Pot.BET_CALL # all-in
		assert game.action == None

		assert game.show_all == True
		assert game.hand_over == False

		game.deck.testing_add_cards(["KH"])
		game.deal_community()
		game.check_for_winners()

		game.evaluate()
		assert game.payouts == [[(2, 4200)]]
		assert self.show_strings(game) == [
		(1, "pair of sixes, king kicker"),
		(2, "pair of kings, queen kicker"),
		]

		game.make_payments()
		assert self.p_jamie.purse == 0
		assert self.p_dave.purse == 6000

		game.finish_hand()
		assert len(game.active_players) == 1
		assert game.game_ended == True
		assert game.places == [(4, 4, 'Chris'), (3, 3, 'Brian'), (2, 1, 'Jamie'), (1, 2, 'Dave')]
