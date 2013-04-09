from pyker.eval import high_card, eval_hands
from pyker.lang import get_hand_phrase
import py.test

def hand_string(pocket, common):
	return get_hand_phrase(eval_hands([["foo", pocket]], common)[0][1])

class TestHands:
	def test_high(self):
		assert hand_string(['AS', '2C'], ['3D', '7D', '9D', 'TD', 'JS']) == 'ace high'

	def test_pair(self):
		assert hand_string(['AS', '2C'], ['3D', '2D', '9D', 'TD', 'JS']) == 'a pair of twos, ace kicker'

	def test_2pair(self):
		assert hand_string(['AS', '2C'], ['3D', '2D', '9D', '3D', 'JS']) == 'two pair of threes and twos'

	def test_set(self):
		assert hand_string(['AS', '2C'], ['3D', '2D', '9D', '2H', 'JS']) == 'a set of twos'

	def test_straight(self):
		assert hand_string(['AS', '2C'], ['3D', '4D', '9D', '5H', '6S']) == 'a straight to the six'

	def test_flush(self):
		assert hand_string(['AS', '2D'], ['3D', '4D', '9D', '5H', '6D']) == 'nine high flush'

	def test_boat(self):
		assert hand_string(['AS', '2D'], ['AD', '4D', '9D', 'AH', '2C']) == 'full house, aces full of twos'

	def test_four(self):
		assert hand_string(['AS', '2D'], ['AD', '4D', '9D', 'AH', 'AC']) == 'quad aces'

	def test_stfl(self):
		assert hand_string(['AS', '2D'], ['AD', '4D', '3D', '5D', '6D']) == 'straight flush to the six'

	def test_stfl(self):
		assert hand_string(['AD', '2D'], ['KD', 'JD', 'QD', 'TD', '6D']) == 'a royal flush'
		

class TestHigh:
	def test_high_single(self):
		assert high_card([("foo", "3S")]) == ("foo", "3S")

	def test_high_set(self):
		assert high_card([("foo", "3S"), ("bar", "JS")]) == ("bar", "JS")

	def test_high_tie(self):
		assert high_card([("foo", "KD"), ("bar", "KS")]) == ('bar', 'KS')
		assert high_card([("foo", "KH"), ("bar", "KC")]) == ('foo', 'KH')
