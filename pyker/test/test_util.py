from pyker.util import *


class TestUtil:
	def test_nep(self):
		assert next_extant_player(3, [1, 2, 3]) == 1
		assert next_extant_player(3, [0, 2, 3]) == 0
		assert next_extant_player(3, [0, 2, 4, 5]) == 4
