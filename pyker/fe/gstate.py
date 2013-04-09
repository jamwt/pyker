from threading import Semaphore

class LockedState:
	def __init__(self):
		self.state = {}
		self._lock = Semaphore()
		self.updated = False

	def update(self, state):
		self.lock()
		self.state = state
		self.updated = True
		self.unlock()

	def lock(self):
		self._lock.acquire()

	def co(self):
		return self.state.copy()

	def unlock(self):
		self._lock.release()
