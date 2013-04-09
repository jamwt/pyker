from pyker.errors import GameError

class Player:
	def __init__(self, nick):
		self.nick = nick
		self.hand = []
		self._in = False
		self.purse = 0
		self.playing = False
		self.sitting = False

	def fund(self, amt):
		self.purse += amt

	def deduct(self, amt):
		self.purse -= amt

	def sit_in(self):
		if self.sitting:
			raise GameError, "player is already sitting"
		self.sitting = True

	def stand_up(self):
		self.sitting = False

	def fold(self):
		self.playing = False

	def give_card(self, card):
		self.playing = True
		self.hand.append(card)

	def discard(self):
		self.hand = []

	def _get_all_in(self):
		if self.purse == 0 and self.playing:
			return True
		return False
	all_in = property(_get_all_in)
