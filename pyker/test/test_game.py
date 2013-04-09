from pyker.game import *


class TestBlindMovement:
	def test_new(self):
		assert round_rotation(1, None, None, [0, 1, 2, 3]) == (1, 2, 3)
		assert round_rotation(2, None, None, [1, 2]) == (2, 2, 1)
		
	def test_simple(self):
		assert round_rotation(0, 1, 2, [0, 1, 2, 3]) == (1, 2, 3)

	def test_rotate(self):
		assert round_rotation(0, 1, 2, [0, 1, 2]) == (1, 2, 0)

	def test_edge(self):
		assert round_rotation(0, 1, 2, [1, 2, 3]) == (1, 2, 3)

	def test_smallbust_4(self):
		assert round_rotation(0, 1, 2, [0, 2, 3]) == (0, 2, 3)

	def test_bigbust_4(self):
		assert round_rotation(0, 1, 2, [0, 1, 3]) == (1, 2, 3)
		assert round_rotation(1, 2, 3, [0, 1, 3]) == (1, 3, 0)

	def test_hu_dealerbust(self):
		assert round_rotation(0, 1, 2, [1, 2]) == (1, 2, 1)
		assert round_rotation(1, 2, 1, [1, 2]) == (1, 1, 2)
		assert round_rotation(1, 1, 2, [1, 2]) == (2, 2, 1)

	def test_hu_smallbust(self):
		assert round_rotation(0, 1, 2, [0, 2]) == (2, 2, 0)
		assert round_rotation(2, 2, 0, [0, 2]) == (0, 0, 2)

	def test_hu_bigbust(self):
		assert round_rotation(0, 1, 2, [0, 1]) == (1, 1, 0)
		assert round_rotation(1, 1, 0, [0, 1]) == (0, 0, 1)

	def test_lotsbust(self):
		assert round_rotation(5, 6, 7, [0, 1, 3, 4, 5]) == (5, 7, 0)
		assert round_rotation(5, 7, 0, [0, 1, 3, 4, 5]) == (5, 0, 1)
		assert round_rotation(5, 0, 1, [0, 1, 3, 4, 5]) == (0, 1, 3)

