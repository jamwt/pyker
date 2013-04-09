from pyker.pot import Pot
from pyker import GameError
import py.test

class TestPotBasic:
	def test_simple(self):
		p = Pot()
		p.new_round(10)
		p.bet(1, 10)
		p.end_round()
		assert p.pots == [(10, [1])]

	def test_multiple(self):
		p = Pot()
		p.new_round(10)
		p.bet(1, 10)
		p.bet(2, 10)
		p.end_round()
		assert p.pots == [(20, [1, 2])]

	def test_too_small(self):
		p = Pot()
		p.new_round(10)
		p.bet(1, 10)
		py.test.raises(GameError, p.bet, 2, 5)

	def test_deficit(self):
		p = Pot()
		p.new_round(10)
		p.bet(1, 10)
		assert p.deficit(2) == 10
		p.bet(2, 25)
		assert p.deficit(1) == 15

	def test_fold(self):
		p = Pot()
		p.new_round(10)
		p.bet(1, 10)
		p.bet(2, 25)
		p.bet(3, 50)
		assert p.deficit(2) == 25
		assert p.deficit(1) == 40
		p.bet(2, 25) # no #1 bet
		p.end_round()
		assert p.pots == [(110, [2, 3])]

class TestPotAdvanced:
	def test_fold_allin(self):
		p = Pot()
		p.new_round(25)
		p.bet(0, 25)
		p.bet(1, 300)
		p.bet(2, 600)
		p.bet(3, 100, all_in=True)
		p.bet(1, 300)
		p.end_round()
		assert p.pots == [(325, [3, 1, 2]), (1000, [1, 2])]

	def test_overpay_sidepot(self):
		p = Pot()
		p.new_round(50)
		p.bet(1, 50)
		p.bet(2, 20, all_in=True)
		p.bet(3, 30, all_in=True)
		p.end_round()
		assert p.pots == [(60, [2, 3, 1]), (20, [3, 1]), (20, [1])]

	def test_multiple_sidepots(self):
		p = Pot()
		p.new_round(10)
		p.bet(1, 10)
		p.bet(2, 10)
		p.bet(3, 7, all_in=True)
		p.bet(4, 20)
		p.bet(1, 2, all_in=True)
		p.bet(2, 30)
		p.bet(4, 20)
		p.end_round()
		assert p.pots == [(28, [3, 1, 2, 4]), (15, [1, 2, 4]), (56, [2, 4])]
