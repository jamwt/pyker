class VirtualTextFormatter:
	def __init__(self, width):
		self.width = width
		self.format = []

	def newline(self, indent_level=0):
		self.format.append([])
		self.indent_level = indent_level
		self.written_width = 0

	def _break(self):
		self.format.append([(' ' * self.indent_level, None)])
		self.written_width = self.indent_level

	def _add_to_line(self, s, xtra):
		self.format[-1].append((s, xtra))
		self.written_width += len(s)

	def add(self, s, xtra=None):
		if s.count(' ') > 1 or (' ' in s and not s.startswith(' ') and not s.endswith(' ')):
			words = s.split(' ')
			for word in words[:-1]:
				self.add(word + ' ', xtra)
			self.add(words[-1], xtra)
		elif len(s) > self.width:
				self._break()
				x = 0
				while True:
					writable = self.width - self.written_width
					self.add(s[x:x + writable], xtra)
					x += writable
					if x > len(s):
						break
					self._break()
		else:
			if len(s) > self.width - self.written_width:
				self._break()
			self._add_to_line(s, xtra)

def test_format(v):
	fstr = '|%%-%ss|' % v.width
	for line in v.format:
		print fstr % ''.join([i[0] for i in line])
